
from constants import PATHS, BASE_URL
#import stock_trade.TradeType
from urllib import parse
import re
from functools import wraps
import inspect
from decimal import Decimal
import copy
import warnings
import datetime
from threading import Thread
import queue
import traceback

class TradeExceedsMaxSharesException(Exception):
    def __init__(self, message, max_shares):
        super().__init__(message)
        self.max_shares = max_shares

def validate_and_execute_trade(trade,adjust_shares=True):
    try:
        trade_info = trade.validate()
    except TradeExceedsMaxSharesException as e:
        if adjust_shares and e.max_shares > 0:
            trade.quantity = e.max_shares
            return validate_and_execute_trade(trade,adjust_shares=False)
        else:
            raise e

    if trade.validated:
        print(trade_info)
        trade.execute()
    else:
        warnings.warn("Unable to validate trade.")

def date_regex(input_date):
    datetime_obj = None
    try:
        # mon_day_year_hour_min_sec_ampm
        date_ints = re.search(r'(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2})\:(\d{1,2})\:(\d{1,2})\s+(AM|PM)',input_date).groups()
        hour = int(date_ints[3])
        if date_ints[6] == 'PM':
            hour += 12
        datetime_obj = datetime.datetime(int(date_ints[2]),int(date_ints[0]),int(date_ints[1]),hour,int(date_ints[5]))
    except Exception as e:
        print("error while parsing order date")
        return input_date

    return datetime_obj
        

def coerce_value(value,new_type):
    if type(value) != str and type(value) == new_type:
        return value
    
    if new_type not in (str,Decimal,int):
        return value
    
    value = re.sub('\s+',' ', str(value)).strip()
    if new_type == str:
        return value

    if new_type == str:
        return value
    
    if new_type == Decimal:
        return Decimal(re.sub(r'[^\-\d\.]+','',value))

    elif new_type == int:
        return int(re.sub(r'[^\d\.\-]+','',value))

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

    routes = PATHS

    @classmethod
    def route(cls, page_name):
        return cls.append_path(BASE_URL, cls.routes[page_name])


class Task(object):
    def __init__(self,*args,**kwargs):
        self.fn = kwargs.pop('fn')
        self.args = args
        self.kwargs = kwargs

    def execute(self):
        try:
            self.fn(*self.args,**self.kwargs)
        except Exception as e:
            print(e)
            traceback.print_exc()


class TaskQueue(object):
    def __init__(self,default_task_function=None):
        self.queue = queue.Queue()
        self.thread = Thread(target=self.worker)
        self.thread.daemon = True
        self.default_task_fn = default_task_function or self._task_fn
        self.thread.start()

    def enqueue(self,*args,**kwargs):
        kwargs.setdefault('fn',self.default_task_fn)
        self.queue.put(Task(*args,**kwargs))

    @staticmethod
    def task_fn(*args,**kwargs):
        raise Exception("No task function defined!  Either override this method or pass a function to the TaskQueue.")

    def worker(self):
        while True:
            task = self.queue.get()
            if task is None:
                self.queue.task_done()
                break
            task.execute()
            self.queue.task_done()

    def finish(self):
        self.queue.put(None)
        self.queue.join()
        self.thread.join()