{
    'name': 'Prime Power Work Order',
    'version': '13',
    'category': "",
    'description': """ Work Order Report 
    """,
    'author':'Xmarts',
    'depends': ['base','sale','primepower_sales_extended'],
    'data': [
	    "report/work_order_report.xml",
        "report/production_work_order_report.xml",
        "views/product_view.xml",
    ],
    'qweb': [
        ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
