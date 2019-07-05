import time
import logging
from functools import wraps

from requests.exceptions import RequestException, ConnectionError, ConnectTimeout, HTTPError


logger = logging.getLogger('storage_robot')

def retry(exceptions, tries=4, delay=5, backoff=2):
    def wrapper(fun):
        @wraps(fun)
        def wrapped(*args, **kwargs):
            final_excep = None
            for i in range(tries):
                if i > 0:
                    nonlocal delay
                    time.sleep(delay)
                    delay *= backoff
                final_excep = None
                
                try:
                    return fun(*args, **kwargs)
                except (exceptions) as e:
                    if e.__class__ == HTTPError:
                        http_status = e.response.status_code
                        error_msg = e.response.json().get('error')

                        if http_status >= 500:
                            logger.warning(f'''http_server_error, http_status={http_status},
                                    http_err_msg={error_msg}, attempt={i+1}, error={e}''')
                            final_excep = e
                        else:
                            # logger.error(
                            #     f'http_server_error, http_status={http_status}, http_err_msg={error_msg}, error={e}')
                            final_excep = e
                            break
                    else:
                        final_excep = e
                        logger.warning(
                            f'attempt={i+1}, error={e}')

            if final_excep is not None:
                raise final_excep
        return wrapped
    
    return wrapper
