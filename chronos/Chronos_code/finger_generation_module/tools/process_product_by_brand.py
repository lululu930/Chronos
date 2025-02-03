#### 按照品牌分类的型号处理，用于解决lmt数据型号或者版本格式与ERT数据不符的情况
import re
from datetime import datetime

def process_url(url):
    """
    处理url，提取路径，去掉可能出现的ip地址和版本
    """

    url = url.split('=')[0].strip()  # 去掉版本以及时间部分
    new_url = url
    pattern = r"^https*://[\d.]+(/.*)"
    # 使用正则表达式去掉IP地址和端口号，只保留路径部分
    # 正则表达式解释:
    # - `^http://`: 匹配以 "http://" 开头的部分。
    # - `[\d.]+`: 匹配 IP 地址部分 (数字和点)。
    # - `(:\d+)?`: 匹配可选的端口号 (冒号加数字)。
    # - `(/.*)`: 匹配从第一个斜杠开始的所有内容并将其捕获为一组。
    pattern = r"^https*://[\d.]+(:\d+)?(/.*)"
    match = re.match(pattern, url)
    if match:
        path_only = match.group(2)  # 获取路径部分
        new_url = path_only
    return new_url


def process_brand_product(brand, product, version, index):
    product_new = product
    version_new = version
    if brand == 'avm':
        if '!' in product_new:
            product_new = product_new.replace('!', '')
        if 'powerline' in product_new:
            product_new = re.sub(r'\s\d+$', '', product_new)
        product_new = product_new.replace(' ', '-')
    if brand == 'cisco':
        # if 'nexus' in product and len(product) == 7:
        #     product = product.replace('-', '@')
        #     tmp = '.'.join([product, version])
        #     product_new, version_new = tmp.split('@')
        if product == 'small business sa540':
            product_new = 'sa540'
        # if product == 'c300v':
        #     product_new = 'email security virtual appliance c300v'
        if 'email security' in product or product in ["c300v", "c600v"]:
            product_new = 'email security'
        if product in ["c3900", "c2900", "c2800nm", "c1900", "c3900e", "c800", "c1841", "c3845", "c850",
                       "c3825", "c890", "c870", "c2951", "c2600", "c2801", "c900", "c860", "c7200p"]:  # 系列路由器
            pass
        if product in ["universalk9-m", "ipbasek9-m", "advipservicesk9-m"]:  # IOS操作系统
            pass
        if product in ["rv320", "rv042", "rv325"]:  # vpn路由器
            pass
        if product in ["wap4410n"]:  # 无线ap
            pass
        if product in ["uc500"]:  # Unified Communications 500
            pass
        if product == 'c3750':  # 交换机
            product_new = 'catalyst 3750'
        if product == 'cat4500e':  # 交换机
            product_new = 'Catalyst 4500e'.lower()
        if product == 'c3560':  # 交换机
            product_new = 'Catalyst 3560'.lower()
        if product == 'c3550':  # nexus 3550系列 or Catalyst 3550系列交换机
            product_new = 'Catalyst 3550'.lower()
        if product == 'c2960':  # 交换机
            product_new = 'Catalyst 2960'.lower()
        if product == 'c2960x':  # 交换机
            product_new = 'catalyst 2960-x'
        if product == 'c3900e':
            product_new = 'c3900'
        if product in ['telepresence sx20', 'telepresence quick set sx20']:
            product_new = 'telepresence sx20 quick set'
        if product in ['telepresence sx10']:
            product_new = 'telepresence sx10 quick set'
        if product == 'small business rv345p':
            product_new = 'rv345p'
        if product == 'nexus_1000v':
            product_new = 'nexus 1000v'
        if product == 'cisco broadworks':
            product_new = 'broadworks'
        if product == 'cisco jabber':
            product_new = 'jabber'
        if product == 'nexus-3':
            product_new = 'cisco nexus 3000 series nx-os'
        # 针对url分析从fofa上手动爬取的数据，需要做特殊处理
        if product == 'firepower':
            product_new = 'firepower 9300'
        if product == 'switch':
            product_new = 'catalyst 2960c'

        if 'aironet  1800s  active sensor cisco wireless' in product:
            product_new = product.replace('aironet  1800s  active sensor cisco wireless',
                                          'aironet 1800s active sensor cisco wireless')
        if 'switches' in product:
            product_new = product.replace('switches', 'switch')
        if 'hosted collaboration solution' in product:
            product_new = 'hosted collaboration solution for contact center'
        if product == 'unified contact center express solution':
            product_new = 'unified contact center enterprise solution'
        if product == 'video surveillance high definition ip camera':
            product_new = 'video surveillance high definition ip cameras'
        if product == 'wireless controller field upgrade software for':
            product_new = 'wireless controller field upgrade software'
        if product in ['wireless controllers and cisco lightweight access points cisco wireless', 'wireless controllers and lightweight access points for', 'wireless controllers and lightweight access points for cisco wireless']:
            product_new = 'wireless controllers and lightweight access points cisco wireless'
        if product == 'wireless ip phone 8821 and 8821-ex':
            product_new = 'wireless ip phone 8821'
        if product.startswith('asyncos'):
            tmp = ' '.join([product, version])
            product_new = tmp.split('for')[-1].strip()
            version_new = tmp.split('for')[0].strip()


    if brand == 'zyxel':
        # if 'zywall' in product:
        #     product = product.replace('zywall', '').strip()
        if 'usg-' in product:
            product = product.replace('usg-', 'usg')
        if 'usg ' in product:
            product = product.replace('usg ', 'usg')
        if 'usgflex' in product:
            product = product.replace('usgflex', 'usg flex')

        if product in ['usg100']:
            product = 'usg flex 100'
        if product == 'usg50':
            product = 'usg flex 50'
        if product == 'usg200':
            product = 'usg flex 200'
        product_new = product
        if product == 'vmg8823-bx0b':
            product_new = 'vmg8823-b50b'
        if product == 'usgflex 100ax':
            product_new = 'usg flex 100ax'
        if index == 'ip_json@n_19881':
            version_new = 'v5.30(absb.4)c0'
        if index == 'ip_json@n_54266':
            version_new = 'v5.13(aaxa.10)c0'
        if index == 'ip_json@n_58218':
            version_new = 'v5.13(abnp.7)c0'
    if brand == 'dahua':
        # if product == 'dh-hcvr5108hs-v4--af-dvr-ii-a-8-1':
        #     product_new = 'dh/hcvr5108h-v2/-af-dvr-ii-a/8-1'
        if product == 'dh-ipc-hfw8239k-z-i4':
            product_new = 'ipc-hfw8239k-z-i4'
        if product == 'dh-psd8839-a180':
            product_new = 'dh-psd8839-h-a180-e5'
        if product == 'dhi-nvr5208-8p-4ks2':
            product_new = 'dhi-nvr5208-4ks2'
        if product == 'dh-hcvr5108hs-v6--af-dvr-ii-a-8-1':
            product_new = 'dh-hcvr5108hs-v6'
        if product == 'dh-hcvr7208a-v4--af-dvr-ii-a-8-4':
            product_new = 'dh/hcvr7208a-v4/-af-dvr-ii-a/8-4'
        if product == 'dh-xvr5116hs-i2':
            product_new = 'dh-xvr5116hs'
        # if product.startswith('dh-'):
        #     product_new = product[3:]
        # if version == '2.420.dahua 00.4.r, build: 2016-05-05':
        #     version_new = '2.420.0000.4.r,build:2016-05-05'
        # if '.dahua' in version and product in ['dh-ipc-hfw4431r-z', 'dh-ipc-hfw1230s']:
        #     version_new = version.replace('.dahua ', '.00000')
        # if '.dahua' in version and product in ['dh-ipc-k35', 'ipc-hfw1020s', 'ipc-kw12w', 'dh-ipc-hfw4200e', 'dh-sd59220s-hn', 'ipc-hfw1300s', 'dh-sd22a204tn-gni',
        #                                        'dh-ipc-hdbw2320r-zs', 'ipc-kw10w', 'dh-ipc-kw100w', 'dh-ipc-hfw4221e', 'dh-ipc-hfw1000s', 'dh-ipc-hfw4100s', 'dh-ipc-k100a',
        #                                        'dh-sd59220t-hn', 'dh-ipc-kw100a', 'ipc-hfw1200s-w', 'dh-ipc-hfw2100', 'dh-sd22204t-gn-w', 'dh-ipc-hfw1220s', 'ipc-hfw3200s']:
        #     version_new = version.replace('.dahua ', '.00')
    if brand == 'hikvision':
        if product == 'ds-7608ni-se':
            product_new = 'ds-7608ni'
        if product == 'ds-7104ni-sn-p':
            product_new = 'ds-7104ni-sn/p'

    if brand == 'synology':
        if index == 'dscan_10@0_59137':
            version_new = '6.2-25556'

    if brand == 'd-link':
        if index == 'cydar_0524_http@cydar_0524_http_2899':
            version_new = '1.11'


    return product_new, version_new


def check_brand_similarity(brand, ert_product, lmt_product, strict_flag=0):
    if brand == 'dahua':
        start_brand = 'dh'
    if brand == 'zyxel':
        start_brand = 'zywall'
    else:
        start_brand = brand
    if ert_product.startswith(start_brand):
        ert_product = ert_product[len(start_brand):].strip()
    if lmt_product.startswith(start_brand):
        lmt_product = lmt_product[len(start_brand):].strip()
    ert_brand_clean = re.sub(r'[^A-Za-z0-9]', '', ert_product)
    lmt_brand_clean = re.sub(r'[^A-Za-z0-9]', '', lmt_product)
    if strict_flag == 2:
        if ert_brand_clean == lmt_brand_clean:
            return True
    elif strict_flag == 1:
        if ert_brand_clean.startswith(lmt_brand_clean) or lmt_brand_clean.startswith(ert_brand_clean) or ert_brand_clean.endswith(lmt_brand_clean) or lmt_brand_clean.endswith(ert_brand_clean):
            return True
    else:
        if ert_brand_clean in lmt_brand_clean or lmt_brand_clean in ert_brand_clean:
            return True
    return False


def get_selected_url_list(group_url_dict, appear_rate, match_rate, analysis_flag=False):
    selected_urls = []

    for k, v in group_url_dict.items():
        if v["count"][2] >= appear_rate and v["match_count"][2] >= match_rate:
            if k not in ['/synoSDSjslib/sds.js?']:
                selected_urls.append(k)
    if not analysis_flag:
        if len(selected_urls) == 0:
            for k, v in group_url_dict.items():
                if v["count"][2] >= 0.9 and v["match_count"][2] >= 0.75:
                    if k not in ['/synoSDSjslib/sds.js?']:
                        selected_urls.append(k)
    # if len(selected_urls) == 0:
    #     for k, v in group_url_dict.items():
    #         if v["count"][2] >= 0.9 and v["match_count"][2] >= 0.75:
    #             if k not in ['/synoSDSjslib/sds.js?']:
    #                 selected_urls.append(k)
    return selected_urls


def re_extract_lmt_in_url(j_line, brand, group_url_dict, appear_rate=0.85, match_rate=0.8, analysis_flag=False):
    """
    1003
    重新从静态资源中更新lmt，header中原来没提出来的，url中包含日期的
    """
    # 正则表达式：匹配 'dlink.css' 且 URL 末尾是日期
    selected_urls = get_selected_url_list(group_url_dict, appear_rate, match_rate, analysis_flag)
    pattern = re.compile(r'dlink\.css.*(\d{4}-\d{2}-\d{2})$')
    # brand = j_line["brand"]
    lmt_day = j_line["lmt"].split(' ')[0]
    new_lmt = j_line["lmt"]
    try:
        lmt_type = j_line["lmt_type"]
    except KeyError:
        lmt_type = ''
    try:
        lmt_list_temp = j_line["lmt_dict"]
    except KeyError:
        lmt_list_temp = j_line["lmt_list"]
    if brand == 'd-link':
        initial_lmt = datetime(1970, 1, 1)
        latest_lmt = initial_lmt
        final_url = ''
        try:
            for k, v in lmt_list_temp.items():
                for url in v:
                    # 匹配并提取日期
                    match = pattern.search(url)
                    if match:
                        date = match.group(1)
                        url_date = datetime.strptime(date, "%Y-%m-%d")
                        # print("提取的日期:", date)
                        # 更新为最晚的日期
                        if url_date > latest_lmt:
                            latest_lmt = url_date
                            final_url = url
            if latest_lmt == initial_lmt or latest_lmt == lmt_day:
                pass
            else:
                new_lmt = str(latest_lmt).split(' ')[0]
                return new_lmt, [final_url]
        except KeyError:
            pass
    if brand == 'zyxel':
        ## zyxel的url在v=后面会接时间，是正确的修改时间
        for k, v in lmt_list_temp.items():
            for url in v:
                if 'v=' in url:
                    extract_time = url.split('v=')[-1]
                    if len(extract_time) == 12:
                        # 将时间字符串解析为 datetime 对象
                        time_format = "%y%m%d%H%M%S"  # 根据给定时间格式解析
                        parsed_time = datetime.strptime(extract_time, time_format)
                        # 格式化为标准时间格式 "YYYY-MM-DD HH:MM:SS"
                        new_lmt = parsed_time.strftime("%Y-%m-%d")
                        if '1970' not in new_lmt:
                            return new_lmt, [url]
    if lmt_type == 'Far' and selected_urls!=[]:
        # 初始时间
        init = datetime.strptime('1970-01-01', '%Y-%m-%d')
        for lmt_time, url_list in lmt_list_temp.items():
            for url in url_list:
                if process_url(url) in selected_urls:
                    if len(str(lmt_time)) > 10:
                        lmt_time = str(lmt_time).split(' ')[0]
                    lmt_time = datetime.strptime(lmt_time, '%Y-%m-%d')
                    if lmt_time > init:
                        init = lmt_time
        if '1970' not in str(init):
            new_lmt = str(init).split(' ')[0]

    else:
        new_lmt = j_line["lmt"]
    return new_lmt, selected_urls

