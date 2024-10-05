def args_join(args):
    return ' '.join([str(x) for x in args])


def Success(*args):
    print(f'SUCCESS\n' + args_join(args))
    return 'SUCCESS\n' + args_join(args)


def Failed(*args):
    print("FAILED\n" + args_join(args))
    return 'FAILED\n' + args_join(args)


def Failure(*args):
    return 'FAILURE\n' + args_join(args)
