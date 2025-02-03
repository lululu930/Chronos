#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import scrapy
import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from tqdm import tqdm
from scrapy.utils.log import configure_logging
from spider_module.myfirstSpider.spiders import dlink_support, axis_os
from spiders import avm, cisco, dahua, dlink, hikvision_cn, netmodule, reolink, synology, teltonika, tplink_dalu, uniview, tplink_tw, hp, mikrotik,hikvision_loudong,dahua_loudong,zyxel, cisco_3850
from spiders import hikvision_en, synology_download_center, axis
from spiders import huawei
from spiders import old_cisco
from spiders import dahua

spider_dict = {
        'avm': avm.AvmSpider,
        'cisco': cisco.CiscoSpider,
        'cisco_3850': cisco_3850.Ciso3850Spider,
        'dahua': dahua.DahuaSpider,
        'dahua_loudong': dahua_loudong.DahuaSpider,
        'dlink': dlink.DlinkSpider,
        'dlink_support': dlink_support.DlinkSpider,
        'hikvision_cn': hikvision_cn.HikvisionSpider,
        'hikvision_en': hikvision_en.HikvisionSpider,
        'hikvision_loudong': hikvision_loudong.HikvisionSpider,
        'hp': hp.HpSpider,
        'huawei': huawei.HuaweiSpider,
        'reolink': reolink.ReolinkSpider,
        'synology': synology.SynologySpider,
        'synology_download_center': synology_download_center.SynologySpider,
        'teltonika': teltonika.TeltonikaSpider,
        'tplink_dalu': tplink_dalu.TplinkSpider,
        'tplink_tw': tplink_tw.TplinkSpider,
        'uniview': uniview.UniviewSpider,
        'zyxel': zyxel.ZyxelSpider,
        'mikrotik': mikrotik.MikrotikSpider,
        'axis': axis.AxisSpider,
        'axis_os': axis_os.AxisOsSpider,
    }


def main(brand):
    # remove log file
    current_dir_path = os.path.dirname(__file__)
    log_file_path = os.path.join(current_dir_path, f"scrapy.log")


    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    
    # start crawling
    process = CrawlerProcess(get_project_settings())
    # process.crawl(teltonika.TeltonikaSpider)
    if brand in spider_dict:
        process.crawl(spider_dict[brand])
    process.start()
    # logging.shutdown()
    # gc.collect()

    # clean log
    close_log_file(log_file_path)


def close_log_file(log_file):
    # ensure the log file to be closed
    import logging
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'baseFilename') and handler.baseFilename == log_file:
            handler.close()
            logging.getLogger().removeHandler(handler)
            print(f"Log file {log_file} closed.")


if __name__ == '__main__':
    # main()
    brand_list = ['cisco']
    # brand_list = spider_dict.keys()
    for brand in tqdm(brand_list, desc='spidering....'):
        main(brand)
        print(f"{brand} done！")

    print("^_^")
