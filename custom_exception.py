from nornir import InitNornir
from nornir.plugins.functions.text import print_result
from nornir.core.task import Result

#only an example, obvisously these are not actual errors.

class MyTaskError(Exception):
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return f"{__class__.__name__}: '{self.message}'"


def my_task(task):
    host = task.host
    changed=False
    try:
        if host.platform == 'ios':
            raise MyTaskError('Silly platform check failed.')
        if host.name == 'srx2':
            raise MyTaskError('Another silly check, because I can.')
    except MyTaskError as e:
        return Result(host=task.host, changed=changed, failed=True, result=f"{e}", exception=f'{e}')
    changed=True
    return Result(host=task.host, changed=changed, failed=False, result=f'Finished: {host}')


def main():
    nr = InitNornir(config_file='../config.yaml')
    #nr = nr.filter(name='cisco3')
    results = nr.run(task=my_task, name="Failure Task Testing")
    print_result(results)
    #import ipdb; ipdb.set_trace()
    print(f'Failed hosts = {results.failed_hosts}')
    print('-'*30)
    for device_name, multi_result in results.items():
        if multi_result.exception:
            print(f'{device_name} had exception: {multi_result.exception}')
  

if __name__ == "__main__":
  main()

