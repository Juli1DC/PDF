{
    'name'       : "Prévision de Trésorerie",
    'summary'    : "Module de gestion des prévisions de trésorerie",
    'discription': "Ce module aidera à la gestion des prévisions de trésorerie",


    'version'    : "16.0.1.0",
    'category'   : "Accounting/accounting",

    'contributors': [
        "1 <Fatima MESSADI>",
        "2 <Yamina ZOUATINE>",

        
        ],


    'company'     : 'Elosys',
    'author'      : 'Elosys',
    'maintainer'  : 'Elosys',


    'support'     : "support@elosys.net",
    'website'     : "http://www.elosys.net/",


    'sequence'   : 1,
    


    'depends': [
        'base',
        'account',
        'stock',
        ],


    'data'   : [
        'data/cron_data.xml',
        'data/action_server.xml',

        'security/ir.model.access.csv',
        'security/planned_money_security.xml',        
        'wizards/lock_planned_money.xml',
        'views/planned_money.xml',
        'views/planned_money_archive.xml',
        'wizards/planned_periodique.xml',
        'views/menu_item.xml',
                ],




    'license'      : "LGPL-3",
    'price'        : "109.99",
    'currency'     : 'Eur',

    'images'       : ['images/banner.gif'],

    'installable' : True,
    'auto_install': False,
    "application" : True,
}

