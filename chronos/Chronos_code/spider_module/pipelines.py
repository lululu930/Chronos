# Define your item pipelines here
from asynchat import simple_producer
from tkinter import Spinbox
from scrapy.exporters import JsonLinesItemExporter
from scrapy.pipelines.files import FilesPipeline
import json
import os
import re
import zipfile
import time
from items import FileItem, Firmware

# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from scrapy.exceptions import DropItem
# import pymysql

pattern_version = re.compile('[ _]([0-9.a-z_]{4,}) ')

class MyfirstspiderPipeline:
    def __init__(self):
        self.names_set = set()


    def open_spider(self, spider):
        file_name = spider.name + "_product.json"
        try:
            f = open(os.path.join("./result_modified_new2", file_name), "r", encoding="utf-8")
            line = f.readline()
            while line:
                try:
                    j_line = json.loads(line)  
                except ValueError:
                    print("data load error!  ip:",line[2:21])
                self.names_set.add(j_line["name"])    
                line = f.readline()
            f.close()
        except Exception as e:
            print(e)

            
    

    #def close_spider(self, spider):
        # self.exporter.finish_exporting()
        #self.fp.close()
    

    def process_item(self, item, spider):
    # def process_item(self, item, spider):
    #     table_name = spider.name
    #     values = (item["model"],item["version"],item["create_time"],item["first_publish_time"],item["crawl_time"],item["name"])
    #     sql = "insert into " + table_name + "(model,version,create_time,first_publish_time,crawl_time,name) values (%s,%s,%s,%s,%s,%s)"
    #     self.db_cursor.execute(sql,values)
    #     return item
    
    # def close_spider(self, spider):
    #     self.db_conn.commit()
    #     self.db_cursor.close()
    #     self.db_conn.close(){
        if item is None: return
        if isinstance(item, FileItem): return
        
        file_name = spider.name + "_product.json"
        if item["name"] in self.names_set:
            raise DropItem("Dulpicate item found: %s " % item)
        else:
            self.names_set.add(item["name"])
            with open(os.path.join("./result_modified_new2", file_name), "a+", encoding="utf-8") as f:
                f.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        
class myFilesPipeline(FilesPipeline):
    time = time.strftime("%Y-%m-%d",time.localtime())
    def item_completed(self, results, item, info):
        valid_file_name = get_valid_file_name(os.path.join(r"D:\spider_download", results[0][1]["path"]))
        if len(valid_file_name) > 1:
            print("file name error!" + str(valid_file_name))
        else:
            # regex
            try:
                version = pattern_version.findall(valid_file_name[0])[0]
            except Exception as e:
                print(e, valid_file_name[0])
            else:
                firmware = Firmware()
                firmware["model"] = item["model"]
                firmware["version"] = version   
                firmware["create_time"] = item["create_time"][0]
                firmware["crawl_time"] = self.time
                firmware["name"] = firmware["model"] + "-" + firmware["version"]  
                firmware["first_publish_time"] = "null" 
                return firmware 
        

def get_valid_file_name(zip_src):
    r = zipfile.is_zipfile(zip_src)
    if r:     
        fz = zipfile.ZipFile(zip_src, 'r')
        valid_file_name = []
        for file_name in fz.namelist():
            if ".bin" in file_name:
                valid_file_name.append(file_name)                
        return valid_file_name  
        
    else:
        print('This is not zip')
