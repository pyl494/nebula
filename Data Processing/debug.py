   
def exception_print(e):
    import traceback, json, sys
    ex_type, ex_value, ex_traceback = sys.exc_info()
    print("Error!\n%s, %s" % (ex_type, ex_value))
    trace_back = traceback.extract_tb(ex_traceback)

    for trace in trace_back:
        print("@%s\n    line %d in  %s \n    %s" % (trace[0], trace[1], trace[2], trace[3]))