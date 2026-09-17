// ============================================================
//  Fragment 70 :: MAIN -- USB descriptors and the main loop
//  (encoder + button + menu).
//  Menu group order: CMD / SUPPORT / AUTH / KEYBOARD
//  (keyboard is always last, its index = 3).
//  NOTE: keep this file pure ASCII.
// ============================================================

// ================= MAIN =================
static int level=0, cur_group=0, cur_item=0;

extern "C" {
uint8_t const* tud_descriptor_device_cb(void){
    static const uint8_t desc[]={18,1,0x00,0x02,0,0,0,64,0x2E,0x8A,0x0A,0x00,0x00,0x01,1,2,3,1}; return desc;
}
uint8_t const* tud_descriptor_configuration_cb(uint8_t i){(void)i;
    static const uint8_t desc[]={9,2,34,0,1,1,0,0x80,250,9,4,0,0,1,0x03,0x01,0x01,0,9,0x21,0x00,0x01,0x00,1,0x22,sizeof(desc_hid_report),0x00,7,5,0x81,0x03,64,0x00,10}; return desc;
}
uint16_t const* tud_descriptor_string_cb(uint8_t i,uint16_t l){(void)l;
    static const char* s[]={"","RP2040","Service Keyboard","123456789ABC"}; static uint16_t b[64];
    if(i>=4)return NULL; const char* str=s[i]; uint8_t len=strlen(str); b[0]=(0x03<<8)|((len*2)+2);
    for(uint8_t j=0;j<len;j++)b[1+j]=str[j]; return b;
}
uint8_t const* tud_hid_descriptor_report_cb(uint8_t i){(void)i; return desc_hid_report;}
uint16_t tud_hid_get_report_cb(uint8_t,uint8_t,hid_report_type_t,uint8_t*,uint16_t){return 0;}
void tud_hid_set_report_cb(uint8_t,uint8_t,hid_report_type_t,uint8_t const*,uint16_t){}
}

int main(){
    set_sys_clock_khz(133000,true); tusb_init();
    gpio_init(11); gpio_set_dir(11,GPIO_OUT); gpio_put(11,1);
    gpio_init(ENC_A);gpio_set_dir(ENC_A,GPIO_IN);gpio_pull_up(ENC_A);
    gpio_init(ENC_B);gpio_set_dir(ENC_B,GPIO_IN);gpio_pull_up(ENC_B);
    gpio_init(ENC_BTN);gpio_set_dir(ENC_BTN,GPIO_IN);gpio_pull_up(ENC_BTN);
    enc_prev=(gpio_get(ENC_A)?2:0)|(gpio_get(ENC_B)?1:0);
    gpio_set_irq_enabled_with_callback(ENC_A,GPIO_IRQ_EDGE_RISE|GPIO_IRQ_EDGE_FALL,true,&gpio_irq_handler);
    gpio_set_irq_enabled(ENC_B,GPIO_IRQ_EDGE_RISE|GPIO_IRQ_EDGE_FALL,true);
    gpio_set_irq_enabled(ENC_BTN,GPIO_IRQ_EDGE_RISE|GPIO_IRQ_EDGE_FALL,true);
    ssd1306_init();
    show_text("SELECT GROUP:",groups[cur_group].name);

    while(true){
        tud_task();
        if(enc_cw){enc_cw=false;
            if(level==0){cur_group=(cur_group+1)%group_count; show_text("SELECT GROUP:",groups[cur_group].name);}
            else{if(cur_group==3){
                    const KeyPage& page = keyboard_pages[kb_page];
                    if (kb_item < page.count - 1) {
                        kb_item++;
                        if (kb_is_vertical_list(page) && kb_item >= kb_offset + 4) kb_offset++;
                    } else {
                        kb_page = (kb_page + 1) % keyboard_page_count;
                        kb_item = 0;
                        kb_offset = 0;
                    }
                    kb_show();
                } else {
                    cur_item = (cur_item + 1) % groups[cur_group].count;
                    show_text(groups[cur_group].name, groups[cur_group].items[cur_item].name);
                }}
        }
        if(enc_ccw){enc_ccw=false;
            if(level==0){cur_group=(cur_group+group_count-1)%group_count; show_text("SELECT GROUP:",groups[cur_group].name);}
            else{if(cur_group==3){
                    const KeyPage& page = keyboard_pages[kb_page];
                    if (kb_item > 0) {
                        kb_item--;
                        if (kb_is_vertical_list(page) && kb_item < kb_offset) kb_offset--;
                    } else {
                        kb_page = (kb_page + keyboard_page_count - 1) % keyboard_page_count;
                        kb_item = keyboard_pages[kb_page].count - 1;
                        kb_offset = kb_is_vertical_list(keyboard_pages[kb_page]) && keyboard_pages[kb_page].count > 4
                            ? keyboard_pages[kb_page].count - 4 : 0;
                    }
                    if (kb_offset < 0) kb_offset = 0;
                    kb_show();
                } else {
                    cur_item = (cur_item + groups[cur_group].count - 1) % groups[cur_group].count;
                    show_text(groups[cur_group].name, groups[cur_group].items[cur_item].name);
                }}
        }
        if(btn_short){btn_short=false;
            if(level==0){level=1;cur_item=0;
                if(cur_group==3){kb_page=0;kb_item=0;kb_offset=0;kb_caps_lock=false;kb_show();}
                else show_text(groups[cur_group].name,groups[cur_group].items[0].name);
            }else{
                if(cur_group==3)kb_send_current();else run_item(groups[cur_group].items[cur_item]);
                if(cur_group!=3)show_text(groups[cur_group].name,groups[cur_group].items[cur_item].name);
            }
            while (gpio_get(ENC_BTN) == 0) sleep_ms(10);
        }
        if(btn_long){btn_long=false;level=0;cur_item=0;show_text("SELECT GROUP:",groups[cur_group].name);}
        sleep_ms(10);
    }
}
