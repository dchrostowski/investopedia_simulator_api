from IPython import embed

from urllib import parse
import re

class Util(object):
    @staticmethod
    def sanitize_number(num_str):
        if type(num_str) == float:
            return num_str
        return float(re.sub(r'(?:\$|\,|\s|\%)', '',num_str))



# Needed this because urllib is a bit clfunky/confusing
class UrlHelper(object):
    @staticmethod
    def append_path(url,path):
        parsed = parse.urlparse(url)
        existing_path = parsed._asdict()['path']
        new_path = "%s%s" % (existing_path,path)
        return UrlHelper.set_field(url,'path',new_path)

    @staticmethod
    def set_path(url,path):
        return UrlHelper.set_field(url,'path',path)

    @staticmethod
    def set_query(url,query_dict):
        query_string = parse.urlencode(query_dict)
        return UrlHelper.set_field(url,'query',query_string)
    
    @staticmethod
    def set_field(url,field,value):
        parsed = parse.urlparse(url)
        # is an ordered dict
        parsed_dict = parsed._asdict()
        parsed_dict[field] = value
        return parse.urlunparse(tuple(v for k,v in parsed_dict.items()))

    @staticmethod
    def get_query_params(url):
        query_str = parse.urlsplit(url).query
        query_params = parse.parse_qsl(query_str)
        return dict(query_params)
