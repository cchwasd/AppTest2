from dataclasses import dataclass


@dataclass
class PageBase:
    package: str = "bao"
    activity: str = "abc"

    class search:
        id="id/search"
        text="搜索"

    class context:
        id="id/context"
        text = "内容"


if __name__ == '__main__':
    obj = PageBase()
    print(PageBase)
    print(obj)
    print(vars(obj))
    print(vars(PageBase))
    print(PageBase.__dict__)
    print(PageBase.search)
    print(PageBase.search.id)
    print(PageBase.search.text)
    print('*'*20)
    from utils import class_to_dict, dict_to_class

    d1 = class_to_dict(PageBase)
    print("类转字典格式：",d1)

    c1 = dict_to_class(d1)
    print("字典转类:",c1)
    print(vars(c1))
    print(c1.search.id,c1.context.id)


