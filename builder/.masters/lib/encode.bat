@echo off
rem ================================================================
rem  RP_COMPILER :: encode.bat -- библиотека токенизации текста.
rem
rem  Точки входа (вызывать через call):
rem     call lib\encode.bat :enc_ascii    -- латиница/цифры/символы
rem                                            (пароли, команды)
rem     call lib\encode.bat :enc_russian  -- русский текст (фразы)
rem
rem  Вход:  ENC_INPUT -- исходная строка.
rem  Выход: ENC_TOKENS -- токены клавиш через запятую
rem           (LAT_*, DIG_*, SYM_*, RU_*),
rem         ENC_ERR -- недопустимый символ (при ошибке).
rem  Коды возврата: 0 = ок, 1 = недопустимый символ, 2 = пусто.
rem
rem  ВАЖНО: работает при ВЫКЛЮЧЕННОМ отложенном раскрытии
rem  (DisableDelayedExpansion) -- благодаря этому символы
rem  ! %% & | < > ^ обрабатываются безопасно.
rem
rem  Соответствие токенов: см. builder\README.md, раздел
rem  "СПРАВОЧНИК ТОКЕНОВ". Токены должны существовать в
rem  ru_keys.h вашего проекта прошивки.
rem ================================================================
exit /b 1

rem ---------------- ЛАТИНИЦА / ЦИФРЫ / СИМВОЛЫ ----------------
:enc_ascii
set "ENC_TOKENS="
set "ENC_ERR="
set "ENC_REST=%ENC_INPUT%"
:ea_loop
if not defined ENC_REST goto :ea_done
set "ENC_CH=%ENC_REST:~0,1%"
set "ENC_REST=%ENC_REST:~1%"
set "ENC_TOK="
rem --- двойная кавычка (через вырезание, сравнением её не взять)
set "ENC_QT=%ENC_CH%"
set "ENC_QT=%ENC_QT:"=%"
if not defined ENC_QT set "ENC_TOK=SYM_DQUOTE"
if "%ENC_CH%"=="a" set "ENC_TOK=LAT_A"
if "%ENC_CH%"=="b" set "ENC_TOK=LAT_B"
if "%ENC_CH%"=="c" set "ENC_TOK=LAT_C"
if "%ENC_CH%"=="d" set "ENC_TOK=LAT_D"
if "%ENC_CH%"=="e" set "ENC_TOK=LAT_E"
if "%ENC_CH%"=="f" set "ENC_TOK=LAT_F"
if "%ENC_CH%"=="g" set "ENC_TOK=LAT_G"
if "%ENC_CH%"=="h" set "ENC_TOK=LAT_H"
if "%ENC_CH%"=="i" set "ENC_TOK=LAT_I"
if "%ENC_CH%"=="j" set "ENC_TOK=LAT_J"
if "%ENC_CH%"=="k" set "ENC_TOK=LAT_K"
if "%ENC_CH%"=="l" set "ENC_TOK=LAT_L"
if "%ENC_CH%"=="m" set "ENC_TOK=LAT_M"
if "%ENC_CH%"=="n" set "ENC_TOK=LAT_N"
if "%ENC_CH%"=="o" set "ENC_TOK=LAT_O"
if "%ENC_CH%"=="p" set "ENC_TOK=LAT_P"
if "%ENC_CH%"=="q" set "ENC_TOK=LAT_Q"
if "%ENC_CH%"=="r" set "ENC_TOK=LAT_R"
if "%ENC_CH%"=="s" set "ENC_TOK=LAT_S"
if "%ENC_CH%"=="t" set "ENC_TOK=LAT_T"
if "%ENC_CH%"=="u" set "ENC_TOK=LAT_U"
if "%ENC_CH%"=="v" set "ENC_TOK=LAT_V"
if "%ENC_CH%"=="w" set "ENC_TOK=LAT_W"
if "%ENC_CH%"=="x" set "ENC_TOK=LAT_X"
if "%ENC_CH%"=="y" set "ENC_TOK=LAT_Y"
if "%ENC_CH%"=="z" set "ENC_TOK=LAT_Z"
if "%ENC_CH%"=="A" set "ENC_TOK=LAT_A_CAP"
if "%ENC_CH%"=="B" set "ENC_TOK=LAT_B_CAP"
if "%ENC_CH%"=="C" set "ENC_TOK=LAT_C_CAP"
if "%ENC_CH%"=="D" set "ENC_TOK=LAT_D_CAP"
if "%ENC_CH%"=="E" set "ENC_TOK=LAT_E_CAP"
if "%ENC_CH%"=="F" set "ENC_TOK=LAT_F_CAP"
if "%ENC_CH%"=="G" set "ENC_TOK=LAT_G_CAP"
if "%ENC_CH%"=="H" set "ENC_TOK=LAT_H_CAP"
if "%ENC_CH%"=="I" set "ENC_TOK=LAT_I_CAP"
if "%ENC_CH%"=="J" set "ENC_TOK=LAT_J_CAP"
if "%ENC_CH%"=="K" set "ENC_TOK=LAT_K_CAP"
if "%ENC_CH%"=="L" set "ENC_TOK=LAT_L_CAP"
if "%ENC_CH%"=="M" set "ENC_TOK=LAT_M_CAP"
if "%ENC_CH%"=="N" set "ENC_TOK=LAT_N_CAP"
if "%ENC_CH%"=="O" set "ENC_TOK=LAT_O_CAP"
if "%ENC_CH%"=="P" set "ENC_TOK=LAT_P_CAP"
if "%ENC_CH%"=="Q" set "ENC_TOK=LAT_Q_CAP"
if "%ENC_CH%"=="R" set "ENC_TOK=LAT_R_CAP"
if "%ENC_CH%"=="S" set "ENC_TOK=LAT_S_CAP"
if "%ENC_CH%"=="T" set "ENC_TOK=LAT_T_CAP"
if "%ENC_CH%"=="U" set "ENC_TOK=LAT_U_CAP"
if "%ENC_CH%"=="V" set "ENC_TOK=LAT_V_CAP"
if "%ENC_CH%"=="W" set "ENC_TOK=LAT_W_CAP"
if "%ENC_CH%"=="X" set "ENC_TOK=LAT_X_CAP"
if "%ENC_CH%"=="Y" set "ENC_TOK=LAT_Y_CAP"
if "%ENC_CH%"=="Z" set "ENC_TOK=LAT_Z_CAP"
if "%ENC_CH%"=="0" set "ENC_TOK=DIG_0"
if "%ENC_CH%"=="1" set "ENC_TOK=DIG_1"
if "%ENC_CH%"=="2" set "ENC_TOK=DIG_2"
if "%ENC_CH%"=="3" set "ENC_TOK=DIG_3"
if "%ENC_CH%"=="4" set "ENC_TOK=DIG_4"
if "%ENC_CH%"=="5" set "ENC_TOK=DIG_5"
if "%ENC_CH%"=="6" set "ENC_TOK=DIG_6"
if "%ENC_CH%"=="7" set "ENC_TOK=DIG_7"
if "%ENC_CH%"=="8" set "ENC_TOK=DIG_8"
if "%ENC_CH%"=="9" set "ENC_TOK=DIG_9"
if "%ENC_CH%"==" " set "ENC_TOK=SYM_SPACE"
if "%ENC_CH%"=="!" set "ENC_TOK=SYM_EXCL"
if "%ENC_CH%"=="@" set "ENC_TOK=SYM_AT"
if "%ENC_CH%"=="#" set "ENC_TOK=SYM_HASH"
if "%ENC_CH%"=="$" set "ENC_TOK=SYM_DOLLAR"
if "%ENC_CH%"=="%" set "ENC_TOK=SYM_PERCENT"
if "%ENC_CH%"=="^" set "ENC_TOK=SYM_CARET"
if "%ENC_CH%"=="&" set "ENC_TOK=SYM_AMP"
if "%ENC_CH%"=="*" set "ENC_TOK=SYM_STAR"
if "%ENC_CH%"=="(" set "ENC_TOK=SYM_LPAREN"
if "%ENC_CH%"==")" set "ENC_TOK=SYM_RPAREN"
if "%ENC_CH%"=="-" set "ENC_TOK=SYM_MINUS"
if "%ENC_CH%"=="_" set "ENC_TOK=SYM_UNDER"
if "%ENC_CH%"=="=" set "ENC_TOK=SYM_EQUAL"
if "%ENC_CH%"=="+" set "ENC_TOK=SYM_PLUS"
if "%ENC_CH%"=="[" set "ENC_TOK=SYM_LBRACK"
if "%ENC_CH%"=="]" set "ENC_TOK=SYM_RBRACK"
if "%ENC_CH%"=="{" set "ENC_TOK=SYM_LBRACE"
if "%ENC_CH%"=="}" set "ENC_TOK=SYM_RBRACE"
if "%ENC_CH%"=="\" set "ENC_TOK=SYM_BSLASH"
if "%ENC_CH%"=="|" set "ENC_TOK=SYM_PIPE"
if "%ENC_CH%"==";" set "ENC_TOK=SYM_SEMI"
if "%ENC_CH%"==":" set "ENC_TOK=SYM_COLON"
if "%ENC_CH%"=="'" set "ENC_TOK=SYM_SQUOTE"
if "%ENC_CH%"=="," set "ENC_TOK=SYM_COMMA"
if "%ENC_CH%"=="<" set "ENC_TOK=SYM_LT"
if "%ENC_CH%"=="." set "ENC_TOK=SYM_DOT"
if "%ENC_CH%"==">" set "ENC_TOK=SYM_GT"
if "%ENC_CH%"=="/" set "ENC_TOK=SYM_SLASH"
if "%ENC_CH%"=="?" set "ENC_TOK=SYM_QMARK"
if "%ENC_CH%"=="~" set "ENC_TOK=SYM_TILDE"
if not defined ENC_TOK goto :ea_err
set "ENC_TOKENS=%ENC_TOKENS%,%ENC_TOK%"
goto :ea_loop
:ea_err
set "ENC_ERR=%ENC_CH%"
set "ENC_TOKENS="
exit /b 1
:ea_done
if not defined ENC_TOKENS exit /b 2
set "ENC_TOKENS=%ENC_TOKENS:~1%"
exit /b 0

rem ---------------- РУССКИЙ ТЕКСТ ----------------
:enc_russian
set "ENC_TOKENS="
set "ENC_ERR="
set "ENC_REST=%ENC_INPUT%"
:er_loop
if not defined ENC_REST goto :er_done
set "ENC_CH=%ENC_REST:~0,1%"
set "ENC_REST=%ENC_REST:~1%"
set "ENC_TOK="
rem --- строчные
if "%ENC_CH%"=="а" set "ENC_TOK=RU_A"
if "%ENC_CH%"=="б" set "ENC_TOK=RU_B"
if "%ENC_CH%"=="в" set "ENC_TOK=RU_V"
if "%ENC_CH%"=="г" set "ENC_TOK=RU_G"
if "%ENC_CH%"=="д" set "ENC_TOK=RU_D"
if "%ENC_CH%"=="е" set "ENC_TOK=RU_E"
if "%ENC_CH%"=="ё" set "ENC_TOK=RU_YO"
if "%ENC_CH%"=="ж" set "ENC_TOK=RU_ZH"
if "%ENC_CH%"=="з" set "ENC_TOK=RU_Z"
if "%ENC_CH%"=="и" set "ENC_TOK=RU_I"
if "%ENC_CH%"=="й" set "ENC_TOK=RU_Y"
if "%ENC_CH%"=="к" set "ENC_TOK=RU_K"
if "%ENC_CH%"=="л" set "ENC_TOK=RU_L"
if "%ENC_CH%"=="м" set "ENC_TOK=RU_M"
if "%ENC_CH%"=="н" set "ENC_TOK=RU_N"
if "%ENC_CH%"=="о" set "ENC_TOK=RU_O"
if "%ENC_CH%"=="п" set "ENC_TOK=RU_P"
if "%ENC_CH%"=="р" set "ENC_TOK=RU_R"
if "%ENC_CH%"=="с" set "ENC_TOK=RU_S"
if "%ENC_CH%"=="т" set "ENC_TOK=RU_T"
if "%ENC_CH%"=="у" set "ENC_TOK=RU_U"
if "%ENC_CH%"=="ф" set "ENC_TOK=RU_F"
if "%ENC_CH%"=="х" set "ENC_TOK=RU_KH"
if "%ENC_CH%"=="ц" set "ENC_TOK=RU_TS"
if "%ENC_CH%"=="ч" set "ENC_TOK=RU_CH"
if "%ENC_CH%"=="ш" set "ENC_TOK=RU_SH"
if "%ENC_CH%"=="щ" set "ENC_TOK=RU_SHCH"
if "%ENC_CH%"=="ъ" set "ENC_TOK=RU_HARD"
if "%ENC_CH%"=="ы" set "ENC_TOK=RU_YI"
if "%ENC_CH%"=="ь" set "ENC_TOK=RU_SOFT"
if "%ENC_CH%"=="э" set "ENC_TOK=RU_E"
if "%ENC_CH%"=="ю" set "ENC_TOK=RU_YU"
if "%ENC_CH%"=="я" set "ENC_TOK=RU_YA"
rem --- прописные
if "%ENC_CH%"=="А" set "ENC_TOK=RU_A_CAP"
if "%ENC_CH%"=="Б" set "ENC_TOK=RU_B_CAP"
if "%ENC_CH%"=="В" set "ENC_TOK=RU_V_CAP"
if "%ENC_CH%"=="Г" set "ENC_TOK=RU_G_CAP"
if "%ENC_CH%"=="Д" set "ENC_TOK=RU_D_CAP"
if "%ENC_CH%"=="Е" set "ENC_TOK=RU_E_CAP"
if "%ENC_CH%"=="Ё" set "ENC_TOK=RU_YO_CAP"
if "%ENC_CH%"=="Ж" set "ENC_TOK=RU_ZH_CAP"
if "%ENC_CH%"=="З" set "ENC_TOK=RU_Z_CAP"
if "%ENC_CH%"=="И" set "ENC_TOK=RU_I_CAP"
if "%ENC_CH%"=="Й" set "ENC_TOK=RU_Y_CAP"
if "%ENC_CH%"=="К" set "ENC_TOK=RU_K_CAP"
if "%ENC_CH%"=="Л" set "ENC_TOK=RU_L_CAP"
if "%ENC_CH%"=="М" set "ENC_TOK=RU_M_CAP"
if "%ENC_CH%"=="Н" set "ENC_TOK=RU_N_CAP"
if "%ENC_CH%"=="О" set "ENC_TOK=RU_O_CAP"
if "%ENC_CH%"=="П" set "ENC_TOK=RU_P_CAP"
if "%ENC_CH%"=="Р" set "ENC_TOK=RU_R_CAP"
if "%ENC_CH%"=="С" set "ENC_TOK=RU_S_CAP"
if "%ENC_CH%"=="Т" set "ENC_TOK=RU_T_CAP"
if "%ENC_CH%"=="У" set "ENC_TOK=RU_U_CAP"
if "%ENC_CH%"=="Ф" set "ENC_TOK=RU_F_CAP"
if "%ENC_CH%"=="Х" set "ENC_TOK=RU_KH_CAP"
if "%ENC_CH%"=="Ц" set "ENC_TOK=RU_TS_CAP"
if "%ENC_CH%"=="Ч" set "ENC_TOK=RU_CH_CAP"
if "%ENC_CH%"=="Ш" set "ENC_TOK=RU_SH_CAP"
if "%ENC_CH%"=="Щ" set "ENC_TOK=RU_SHCH_CAP"
if "%ENC_CH%"=="Ъ" set "ENC_TOK=RU_HARD_CAP"
if "%ENC_CH%"=="Ы" set "ENC_TOK=RU_YI_CAP"
if "%ENC_CH%"=="Ь" set "ENC_TOK=RU_SOFT_CAP"
if "%ENC_CH%"=="Э" set "ENC_TOK=RU_E_CAP"
if "%ENC_CH%"=="Ю" set "ENC_TOK=RU_YU_CAP"
if "%ENC_CH%"=="Я" set "ENC_TOK=RU_YA_CAP"
rem --- цифры
if "%ENC_CH%"=="0" set "ENC_TOK=DIG_0"
if "%ENC_CH%"=="1" set "ENC_TOK=DIG_1"
if "%ENC_CH%"=="2" set "ENC_TOK=DIG_2"
if "%ENC_CH%"=="3" set "ENC_TOK=DIG_3"
if "%ENC_CH%"=="4" set "ENC_TOK=DIG_4"
if "%ENC_CH%"=="5" set "ENC_TOK=DIG_5"
if "%ENC_CH%"=="6" set "ENC_TOK=DIG_6"
if "%ENC_CH%"=="7" set "ENC_TOK=DIG_7"
if "%ENC_CH%"=="8" set "ENC_TOK=DIG_8"
if "%ENC_CH%"=="9" set "ENC_TOK=DIG_9"
rem --- знаки препинания
if "%ENC_CH%"==" " set "ENC_TOK=RU_SPACE"
if "%ENC_CH%"=="," set "ENC_TOK=RU_COMMA"
if "%ENC_CH%"=="." set "ENC_TOK=RU_DOT"
if "%ENC_CH%"=="-" set "ENC_TOK=SYM_MINUS"
if "%ENC_CH%"==":" set "ENC_TOK=SYM_COLON"
if "%ENC_CH%"=="!" set "ENC_TOK=SYM_EXCL"
if "%ENC_CH%"=="?" set "ENC_TOK=SYM_QMARK"
if not defined ENC_TOK goto :er_err
set "ENC_TOKENS=%ENC_TOKENS%,%ENC_TOK%"
goto :er_loop
:er_err
set "ENC_ERR=%ENC_CH%"
set "ENC_TOKENS="
exit /b 1
:er_done
if not defined ENC_TOKENS exit /b 2
set "ENC_TOKENS=%ENC_TOKENS:~1%"
exit /b 0
