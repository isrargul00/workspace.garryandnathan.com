{
    'name': "Create Authorize.net Profiles",
    'summary': """Adds functionality to create Authorize.net customer and payment profiles.""",
    'author': "Israr",
    'website': "https://www.fiverr.com/isrargul00",
    'version': '1.0',
    'depends': [
        'base',
        'payment', 'account_payment'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_inherit.xml',
        'wizard/create_authorize_profile.xml'],
    "currency": "USD",
    "price": 20.0,
    'installable': True,
    "auto_install": False,
    "application": True,
}
