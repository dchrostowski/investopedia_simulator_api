import re
from functools import wraps
import inspect
from decimal import Decimal
import copy
        

def coerce_value(value,new_type):
    if type(value) != str and type(value) == new_type:
        return value
    
    if new_type not in (str,Decimal,int):
        return value
    
    value = re.sub(r'\s+',' ', str(value)).strip()
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
            # warnings.warn("Missing annotations for param(s).  Not correcting any param types for method %s" % func.__qualname__)
            return func(self,*args,**kwargs)
        return func(self,**new_kwargs)
    return wrapper