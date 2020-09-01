import traceback, json, sys, html

def exception_print(e):
    ex_type, ex_value, ex_traceback = sys.exc_info()
    print("Error!\n%s(%s|%s|%s), %s" % (ex_type,e.__class__.__name__, type(e).__name__, e.__class__.__qualname__, ex_value))
    trace_back = traceback.extract_tb(ex_traceback)

    for trace in trace_back:
        print("@%s\n    line %d in  %s \n    %s" % (trace[0], trace[1], trace[2], trace[3]))

def exception_html(e):
    exception_print(e)

    import traceback
    ex_type, ex_value, ex_traceback = sys.exc_info()
    trace_back = traceback.extract_tb(ex_traceback)
    stack_trace = list()
    for trace in trace_back:
        stack_trace.append("<b>@%s</b><br/>    line %d in  %s <br/>    %s" % (html.escape(trace[0]), trace[1], html.escape(trace[2]), html.escape(trace[3])))

    return "<div>%s (%s | %s | %s), %s<br/><pre>%s</pre></div>" % (ex_type, ex_value, e.__class__.__name__, type(e).__name__, e.__class__.__qualname__, json.dumps(stack_trace, indent=2))
