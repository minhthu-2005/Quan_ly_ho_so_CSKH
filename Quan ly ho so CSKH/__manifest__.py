{
    'name': 'Quản lý hồ sơ CSKH',
    'version': '1.0',
    'summary': 'Quản lý lịch sử tương tác và chăm sóc khách hàng',
    'category': 'CRM',
    'depends': [
        'crm',
        'mail',
    ],

    'data': [

        'security/security.xml',
        'security/ir.model.access.csv',

        'data/sequence.xml',
        'data/cron_job.xml',

        'views/menu_views.xml',
        'views/crm_interaction_history_views.xml',
        'views/crm_lead_views.xml',
    ],

    'installable': True,
    'application': True,
}