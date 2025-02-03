import re
from datetime import datetime

def process_url(url):
    """
    process url
    """

    url = url.split('=')[0].strip()
    new_url = url
    pattern = r"^https*://[\d.]+(/.*)"
    pattern = r"^https*://[\d.]+(:\d+)?(/.*)"
    match = re.match(pattern, url)
    if match:
        path_only = match.group(2)
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
        if product == 'small business sa540':
            product_new = 'sa540'
        if 'email security' in product or product in ["c300v", "c600v"]:
            product_new = 'email security'

        if product in ["universalk9-m", "ipbasek9-m", "advipservicesk9-m"]:  # IOS
            pass
        if product == 'c3750':
            product_new = 'catalyst 3750'
        if product == 'cat4500e':
            product_new = 'Catalyst 4500e'.lower()
        if product == 'c3560':
            product_new = 'Catalyst 3560'.lower()
        if product == 'c3550':
            product_new = 'Catalyst 3550'.lower()
        if product == 'c2960':
            product_new = 'Catalyst 2960'.lower()
        if product == 'c2960x':
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


    if brand == 'zyxel':
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
    if brand == 'dahua':
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
    if brand == 'hikvision':
        if product == 'ds-7608ni-se':
            product_new = 'ds-7608ni'
        if product == 'ds-7104ni-sn-p':
            product_new = 'ds-7104ni-sn/p'

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
    extract lmt in url
    """

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
                    match = pattern.search(url)
                    if match:
                        date = match.group(1)
                        url_date = datetime.strptime(date, "%Y-%m-%d")
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
        for k, v in lmt_list_temp.items():
            for url in v:
                if 'v=' in url:
                    extract_time = url.split('v=')[-1]
                    if len(extract_time) == 12:
                        time_format = "%y%m%d%H%M%S"
                        parsed_time = datetime.strptime(extract_time, time_format)
                        new_lmt = parsed_time.strftime("%Y-%m-%d")
                        if '1970' not in new_lmt:
                            return new_lmt, [url]
    if lmt_type == 'Far' and selected_urls!=[]:
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

