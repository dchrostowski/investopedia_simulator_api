
from constants import Constants
#import stock_trade.TradeType
from IPython import embed


from urllib import parse
import re

from functools import wraps
import inspect
from decimal import Decimal
import copy
import warnings

def coerce_value(value,new_type):
    if new_type not in (str,Decimal,int):
        return value
    
    value = re.sub('\s+',' ', str(value)).strip()
    if new_type == str:
        return value

    if new_type == str:
        return value
        
    if new_type == Decimal:
        return Decimal(re.sub(r'[^\d\.]+','',value))

    elif new_type == int:
        return int(re.sub(r'[^\d\.]+','',value))

# Allows child classes to inherit methods but prevents parent class from
def subclass_method(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        method_orig_class = re.search(
            r'^(.+)\.' + re.escape(func.__name__) + r'$', func.__qualname__).group(1)
        if self.__class__.__name__ == method_orig_class:
            raise Exception("Only child classes may call this method.")
        return func(self, *args, **kwargs)
    return wrapper

def coerce_method_params(func):
    @wraps(func)
    def wrapper(self,*args,**kwargs):
        copy_kwargs = copy.deepcopy(kwargs)
        copy_kwargs.update(dict(zip(func.__code__.co_varnames[1:], args)))
        func_annotations = inspect.getfullargspec(func).annotations
        try:
            new_kwargs = {k:coerce_value(copy_kwargs[k], func_annotations[k]) for k in copy_kwargs}
        except KeyError as e:
            warnings.warn("Missing annotations for param(s).  Not correcting any param types for method %s" % func.__qualname__)
            return func(self,*args,**kwargs)
        return func(self,**new_kwargs)
    return wrapper



class Util(object):
    @staticmethod
    def sanitize_number(num_str):
        if type(num_str) == float:
            return num_str
        return float(re.sub(r'(?:\$|\,|\s|\%)', '', num_str))

        



# Needed this because urllib is a bit clfunky/confusing
class UrlHelper(object):
    @staticmethod
    def append_path(url, path):
        parsed = parse.urlparse(url)
        existing_path = parsed._asdict()['path']
        new_path = "%s%s" % (existing_path, path)
        return UrlHelper.set_field(url, 'path', new_path)

    @staticmethod
    def set_path(url, path):
        return UrlHelper.set_field(url, 'path', path)

    @staticmethod
    def set_query(url, query_dict):
        query_string = parse.urlencode(query_dict)
        return UrlHelper.set_field(url, 'query', query_string)

    @staticmethod
    def set_field(url, field, value):
        parsed = parse.urlparse(url)
        # is an ordered dict
        parsed_dict = parsed._asdict()
        parsed_dict[field] = value
        return parse.urlunparse(tuple(v for k, v in parsed_dict.items()))

    @staticmethod
    def get_query_params(url):
        query_str = parse.urlsplit(url).query
        query_params = parse.parse_qsl(query_str)
        return dict(query_params)

    routes = Constants.PATHS

    @classmethod
    def route(cls, page_name):
        return cls.append_path(Constants.BASE_URL, cls.routes[page_name])
