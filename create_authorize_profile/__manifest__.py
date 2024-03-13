{
    'name': "Create Authorize.net Profiles",
    'summary': """Adds functionality to create Authorize.net customer and payment profiles.""",
    'author': "Tom Lowe",
    'version': '1.0',
    'depends': [
            'base',
            'payment'],
    'data': [
            'views/res_partner_inherit.xml',
            'wizard/create_authorize_profile.xml'],
}