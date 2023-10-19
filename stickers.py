import random

stickers = ['CAACAgIAAxkBAAEBbmhlJ_SC31MaSBxq7KRAoW3kUalYjQACbxYAAuBMGEiru0ouJc6voDAE',
            'CAACAgIAAxkBAAEBbmplJ_SHvSXMTgABNZOmQFQzXRmQqh0AAmIXAAJi9xhIxtN_7yFO8YowBA',
            'CAACAgIAAxkBAAEBbmxlJ_SJ-9GG9nEbhFfdYb_ToqHBVQAChxYAAsIaGEhH9pOMLmYe7DAE',
            'CAACAgIAAxkBAAEBbm5lJ_SLwSmjcaYWLjoosGDFjG8MwQAC8xgAAmFOGEiFyL35tfbWOTAE',
            'CAACAgIAAxkBAAEBbnBlJ_SNcdsFHP2nXNcPJF-p4zzt4AAC9BcAAop8IEgmgbl30zIBnTAE',
            'CAACAgIAAxkBAAEBbnJlJ_SP6KYrUYsUdNf-vF0DIMWyjAACfRQAAoYbGUgOOd7NDIpkizAE',
            'CAACAgIAAxkBAAEBbndlJ_SQE_0XO4I_USiL1XmfSYCMjwACURMAAthWIUiA1tB7sjhAojAE',
            'CAACAgIAAxkBAAEBbnplJ_SS6wk8t9-MeeQ2xDfmhX8wQwACQhgAAg12IUhupRp6c-ln_TAE',
            'CAACAgIAAxkBAAEBbnxlJ_SUh015sxepqXX6heGIoO9D0AACaxMAAknfIUhYz3F91OQyZDAE',
            'CAACAgIAAxkBAAEBbn5lJ_SW8PTbh3aCcQwvhXy-AfuJqgACohoAAm9vIUgeo6v_hwK2EzAE']

async def get_random_cat():
    return stickers[random.randint(0, 9)]