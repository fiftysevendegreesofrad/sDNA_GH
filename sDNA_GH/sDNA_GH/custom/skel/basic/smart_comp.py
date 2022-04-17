#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '0.02'


import logging
import sys
from collections import OrderedDict, defaultdict
from inspect import currentframe, getargspec
from abc import abstractmethod
if sys.version < '3.4':
    from abc import ABCMeta
    class ABC:
        __metaclass__ = ABCMeta
else:
    from abc import ABC
if sys.version < '3.3':
    from collections import Callable
else:
    from collections.abc import Callable


from ghpythonlib.componentbase import executingcomponent as component


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def get_args_spec(callable):
    if not isinstance(callable, Callable):
        raise TypeError('Argument is not callable, therefore has no args')
    # assert hasattr(callable, '__call__')
    try:
        arg_spec = getargspec(callable)
    except:
        try:
            arg_spec = getargspec(callable.__call__)
        except:
            raise Exception("Could not get argspec for " + str(callable))
    
    if arg_spec.args[0] in ('self', 'cls'):
        arg_spec = arg_spec._replace(args = arg_spec.args[1:])
    return arg_spec



    # if (type(callable).__name__ == 'function' or
    #     callable.__class__.__name__ == ('function','instancemethod') or
    #     quacks_like(basic_function, callable)):
    #     return getargspec(callable)
    # elif hasattr(callable, '__call__'):

def get_val(key, sources):
    #type(str, list) -> type[any]
    for source in sources:
        if isinstance(source, dict) and key in source:
            return source[key]
        elif hasattr(source, key):
            return getattr(source, key)
    return 'No variable or field: ' + key + ' found. '


def custom_retvals(retval_names, sources = [], return_locals = False, frames_back = 1):
    #type(list[str], list, bool) -> tuple(type[any])
    """ To get inspect.currentframe to target the correct scope,
        if you wrap this function in n functions, that are called from the target
        call it with frames_back = n"""
    if return_locals:
        calling_frame = currentframe()
        for _ in range(frames_back):
            calling_frame = calling_frame.f_back
        sources += [ calling_frame.f_locals.copy() ]
        logger.debug(sources)
    return tuple(get_val(retval_name, sources) for retval_name in retval_names)


def component_Outputs(self, sources):
    
    return custom_retvals([param.NickName for param in self.Params.Output]
                         
                         ,sources
                         ,return_locals = True
                         ,frames_back = 2
                         )



def prepare_args(function
                ,params_dict
                ,anon_pos_args = None
                ,anon_kwargs = None
                ,prioritise_kwargs = True
                ):
    #type(function) -> tuple, dict
    argspec = get_args_spec(function)
    logger.debug('argspec(function) == ' + str(argspec))
    assert isinstance(params_dict, dict), 'OrderedDict of input args required. '
    if not isinstance(params_dict, OrderedDict):
        logger.warning('Order of input arguments may not be preserved.  ')
    params_dict = params_dict.copy()  #We'll be popping keys out later

    args_dict = {}
    pos_args = defaultdict(default_factory = tuple) # positional arguments
    unnamed_pos_args = ()
    req_pos_args = argspec.args

    if argspec.defaults:
        req_pos_args = req_pos_args[:-len(argspec.defaults)]
        # required positional arguments (i.e. before those with default values)

    logger.debug('required positional arguments == ' + str(req_pos_args))
    
    missing_req_pos_args = []
    

    for param_name in req_pos_args:  # Try to fill required positional
                                        # args with names in Params.
        if param_name in params_dict:
            pos_args[param_name] += (params_dict.pop(param_name),)
        else:
            missing_req_pos_args += [param_name]

    
    for param_name in params_dict:   # Try to fill other named args
                                        # with names in Params.
        if param_name in argspec.args: 
            assert param_name not in req_pos_args # i.e., it has a 
                                                    # default value
                                                    # so occurs after
                                                    # req_pos_args
            args_dict[param_name] = params_dict.pop(param_name)
        elif prioritise_kwargs and argspec.keywords:
            if param_name in anon_kwargs:
                args_dict[param_name] = params_dict.pop(param_name)
            elif param_name in anon_pos_args and argspec.varargs:
                unnamed_pos_args += (params_dict.pop(param_name),)
            #else:  unnamed_pos_args == anon_kwargs == [] etc. 
            #       handled later
                
                # Should really prioritise missing_req_pos_args and
                # this could put the positional args out of order, but 
                # as we always have a param name, if it matches a given
                # anon_pos_arg name, and the user wanted it to go to a 
                # named positional argument instead, 
                # what was the point in using this at all?
                # GH components already support *args, so it's just 
                # an edge case we will ignore - this smart component 
                # will never be foolproof!  We can't fix bad naming,
                # and this tool was intended for different usage.
        elif not prioritise_kwargs:
            if param_name in anon_pos_args and argspec.varargs:
                unnamed_pos_args += (params_dict.pop(param_name))
            elif param_name in anon_kwargs and argspec.keywords:
                args_dict[param_name] = params_dict.pop(param_name)
            #else:  unnamed_pos_args == anon_kwargs == [] etc. 
            #       handled later

    assert all(name not in (argspec.args + anon_kwargs + anon_pos_args)
                for name in params_dict
                )
    
    #Try to assign params whose names could not be found to
    # missing required positional args (before ones with defaults).
    if argspec.varargs:
        for req_pos_arg, param_name in zip(missing_req_pos_args, params_dict):
            if missing_req_pos_args:
                pos_args[req_pos_arg] = params_dict.pop(param_name)
                missing_req_pos_args.remove(req_pos_arg)
            else:
                break

    if missing_req_pos_args:
        msg = 'Missing named positional argument'
        logger.warning(msg)
        raise TypeError(msg)
    

    if prioritise_kwargs and argspec.keywords:
        logger.debug('Adding all remaining Input Params to args_dict')
        args_dict.update(params_dict)
    elif  argspec.varargs:
        unnamed_pos_args += tuple(params_dict.values())
        logger.debug('Adding all remaining Input Params to unnamed_pos_args')
    elif params_dict:
        logger.error('Could not allocate Input Params to args : ' + str(params_dict))
    else:
        logger.warning('Inconsistent vargs / kwargs with priority bool')


    unnamed_pos_args = tuple(pos_args.values()) + unnamed_pos_args

    logger.debug('unnamed_pos_args == ' + str(unnamed_pos_args))
    logger.debug('args_dict' + str(args_dict))

    return unnamed_pos_args, args_dict


def custom_inputs_class_deco(BaseComponent
                            ,anon_pos_args = None
                            ,anon_kwargs = None
                            ,prioritise_kwargs = True
                            ):
    #type(type[any], list, list, bool) -> type[any]


    if anon_pos_args is None:
            anon_pos_args = []

    if anon_kwargs == None:
            anon_kwargs = []

    class Decorated(BaseComponent):
    
        main = BaseComponent.RunScript

        def RunScript(self, *param_vals):
            param_names = [param.Name for param in self.Params.Input]
            params_dict = OrderedDict( zip(param_names, param_vals))
            logger.debug('Params_dict == ' + str(params_dict))


            pos_args, args_dict = prepare_args(self.main
                                              ,params_dict = params_dict
                                              ,anon_pos_args = anon_pos_args
                                              ,anon_kwargs = anon_kwargs
                                              ,prioritise_kwargs = prioritise_kwargs   
                                              )

 

            return self.main(*pos_args, **args_dict)
            # BaseClass.RunScript needs to call:
            # component_Outputs(on its retvals) itself
    return Decorated


class MyComponentWithMainABC(component, ABC):
    """Framework for a 'smart' grasshopper component, supporting kwargs type 
       inputs from user-customisable Input Params, default values,
       and returning suitable
       outputs based on the user specified Output Params.  """
    @abstractmethod
    def main(self, *args, **kwargs):
        """ Specify the main script / method here instead of RunScript. 
            In an instance of CustomInputsComponentABC or in a class produced
            by the custom_inputs_class_deco decorator, RunScript now inspects 
            the call signature of this method, then parses the components 
            input Param's matching them up accordingly, then calls this method.

            To also use Custom Outputs in your own code, you need to add the 
            method component_Outputs to the component, in 
            your own code end each exit point of main with
            'return self.component_Outputs(sources)' with 
            sources as a list of whichever dicts or namedtuples whose contents 
            you wish to make available on the Output params.
            
            By default the locals in the scope of main are added to sources so
            sources can be omitted.  
            
            Returning primitives is not supported - 
            create a local variable in the function body with the same name as
            the Output Param you want it on, and assign the primitive to it."""
        return kwargs

    @abstractmethod
    def RunScript(self, *args):
        """The normal method called by Grasshopper when Param Inputs update 
           etc.  A normal component RunScript method can be renamed and saved, 
           then overridden using the custom_inputs_class_deco decorator on the 
           class, in order to use allow the normal RunScript MEthod to adjust 
           its args according to custom Param inputs, and utilise them akin 
           to **kwargs"""
    # type (bool, str, Rhino Geometry, datatree, tuple(namedtuple,namedtuple), *dict)->bool, str, Rhino_Geom, datatree, str

CustomInputsComponentABC = custom_inputs_class_deco(MyComponentWithMainABC)

SmartComponent = custom_inputs_class_deco(MyComponentWithMainABC)
SmartComponent.component_Outputs = component_Outputs



# def old_smart_RunScript(self, *args):
#     args_dict = {key.Name : val for key, val in zip(self.Params.Input, args) } # .Input[4:] type: ignore
#     logger.debug(args)
#     ret_vals_dict = self.main(**args_dict)
#     go = args_dict.get('go', False)

