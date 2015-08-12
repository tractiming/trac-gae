import requests
import datetime
import time


UPDATE_URL = "http://www.trac-us.appspot.com/api/updates/"
#UPDATE_URL = "http://localhost:8000/api/updates/"





def post_split(reader_code, tag_code, time):
    
    formatted_time = time.strftime("%Y/%m/%d %H:%M:%S.%f") 
    payload = {'r': reader_code,
               's': r"[['{0}', '{1}'],]".format(tag_code, formatted_time)}
    r = requests.post(UPDATE_URL, data=payload)
    print r.content



def main():
    tag_str = '12345'
    reader_str = 'A1010'
    all_tags = ['test %04d' %i for i in range(1,51)]


    while True:
        for tag in all_tags:
            post_split(reader_str, tag, datetime.datetime.now())
        print 'splits posted ------------------------'

        time.sleep(40)
    
    #print all_tags
    #post_split(reader_str, tag_str, datetime.datetime.utcnow())


if __name__ == "__main__":
    main()


