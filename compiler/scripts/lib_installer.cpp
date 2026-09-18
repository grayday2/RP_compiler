// Windows host utility; build separately with a Windows C++17 compiler.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
const std::vector<std::string> skipDirs = {
    "examples", "tests", "docs", "test", ".git", "build"
};
const std::vector<std::string> goodExts = {".h", ".c", ".cpp", ".s"};

std::string toLower(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(),
                   [](unsigned char c) { return std::tolower(c); });
    return value;
}
bool hasGoodExt(const fs::path& path) {
    const auto ext = toLower(path.extension().string());
    return std::find(goodExts.begin(), goodExts.end(), ext) != goodExts.end();
}
bool containsSkipDir(const fs::path& path) {
    for (const auto& component : path) {
        const auto name = toLower(component.string());
        if (std::find(skipDirs.begin(), skipDirs.end(), name) != skipDirs.end())
            return true;
    }
    return false;
}
void collectFiles(const fs::path& root, std::vector<fs::path>& files) {
    for (auto it = fs::recursive_directory_iterator(root);
         it != fs::recursive_directory_iterator(); ++it) {
        // Do not follow symlinks/junctions outside the supplied library.
        const DWORD attrs = GetFileAttributesW(it->path().c_str());
        if (attrs == INVALID_FILE_ATTRIBUTES)
            throw std::runtime_error("Cannot read file attributes");
        if (attrs & FILE_ATTRIBUTE_REPARSE_POINT) {
            it.disable_recursion_pending();
            continue;
        }
        const auto relative = it->path().lexically_relative(root);
        if (it->is_directory()) {
            if (containsSkipDir(relative)) it.disable_recursion_pending();
        } else if (it->is_regular_file() && hasGoodExt(it->path())) {
            files.push_back(relative);
        }
    }
    std::sort(files.begin(), files.end());
}
std::string chooseMainHeader(const std::vector<fs::path>& files,
                             const fs::path& name, const fs::path& destination) {
    std::vector<fs::path> headers;
    for (const auto& file : files)
        if (toLower(file.extension().string()) == ".h") headers.push_back(file);
    if (headers.empty()) {
        const auto header = fs::path(name.string() + ".h");
        std::ofstream out(destination / header);
        out << "// Placeholder only: add declarations required by your library.\n#pragma once\n";
        out.close();
        if (!out) throw std::runtime_error("Cannot create header");
        return header.generic_string();
    }
    const auto wanted = toLower(name.string() + ".h");
    for (const auto& header : headers)
        if (toLower(header.filename().string()) == wanted)
            return header.generic_string();
    for (const auto& source : files) {
        const auto ext = toLower(source.extension().string());
        if (ext != ".c" && ext != ".cpp") continue;
        auto candidate = source;
        candidate.replace_extension(".h");
        for (const auto& header : headers)
            if (toLower(header.generic_string()) == toLower(candidate.generic_string()))
                return header.generic_string();
    }
    return headers.front().generic_string();
}
int main() {
    try {
        std::vector<wchar_t> buffer(32768);
        const DWORD size = GetModuleFileNameW(nullptr, buffer.data(),
                                             static_cast<DWORD>(buffer.size()));
        if (!size || size >= buffer.size())
            throw std::runtime_error("Cannot determine executable path");
        const auto root = fs::path(std::wstring(buffer.data(), size)).parent_path();
        const auto tmpDir = root / "tmp";
        const auto libDir = root / "libraries";
        const auto logFile = libDir / "added_libs.txt";
        fs::create_directories(tmpDir);
        fs::create_directories(libDir);
        std::vector<std::string> logLines;
        std::ifstream log(logFile);
        for (std::string line; std::getline(log, line);) logLines.push_back(line);
        log.close();
        std::cout << "RP2040 Portable Library Installer\n";
        bool failed = false;
        for (const auto& entry : fs::directory_iterator(tmpDir)) {
            const DWORD attrs = GetFileAttributesW(entry.path().c_str());
            if (attrs == INVALID_FILE_ATTRIBUTES) {
                failed = true;
                continue;
            }
            if ((attrs & FILE_ATTRIBUTE_REPARSE_POINT) || !entry.is_directory()) continue;
            const auto name = entry.path().filename();
            if (containsSkipDir(name)) continue;
            const auto destination = libDir / name;
            const auto prefix = name.string() + " -> ";
            const bool logged = std::any_of(logLines.begin(), logLines.end(),
                [&](const std::string& line) { return line.rfind(prefix, 0) == 0; });
            if (logged || fs::exists(destination)) {
                std::cout << name.string() << ": already installed, skipping\n";
                continue;
            }
            bool created = false;
            bool installed = false;
            try {
                std::vector<fs::path> files;
                collectFiles(entry.path(), files);
                if (files.empty()) {
                    std::cout << name.string() << ": no source/header files\n";
                    continue;
                }
                created = fs::create_directory(destination);
                if (!created) throw std::runtime_error("Destination already exists");
                for (const auto& relative : files) {
                    fs::create_directories((destination / relative).parent_path());
                    fs::copy_file(entry.path() / relative, destination / relative);
                }
                const auto header = chooseMainHeader(files, name, destination);
                installed = true;
                std::ofstream out(logFile, std::ios::app);
                out << prefix << header << '\n';
                out.close();
                if (!out) throw std::runtime_error("Files installed, but log write failed");
                std::cout << name.string() << ": " << files.size()
                          << " files installed; header: " << header << '\n';
            } catch (const std::exception& error) {
                failed = true;
                if (created && !installed) {
                    std::error_code ignored;
                    fs::remove_all(destination, ignored);
                }
                std::cerr << name.string() << ": " << error.what() << '\n';
            }
        }
        return failed ? 1 : 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
