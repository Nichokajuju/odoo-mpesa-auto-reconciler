<<<<<<< HEAD
# Odoo 18 M-Pesa Auto Reconciler

An Odoo 18 module that automatically matches and reconciles M-Pesa transactions against customer invoices, creating real accounting payments and marking invoices as Paid.

## Features

- Store incoming M-Pesa transactions
- Match transactions to customer invoices by reference or amount
- Automatically create and post Odoo payments
- Reconcile journal entries — invoice flips to **PAID**
- Chatter tracking on every state change
- Color-coded list view (green = reconciled, red = failed)

## Reconciliation Flow
## Installation

1. Clone this repo into your Odoo custom addons folder:
```bash
git clone https://github.com/Nichokajuju/odoo-mpesa-auto-reconciler.git
```

2. Add the path to your `odoo.conf`:
## Installation

1. Clone this repo into your Odoo custom addons folder:
```bash
git clone https://github.com/Nichokajuju/odoo-mpesa-auto-reconciler.git
```

2. Add the path to your `odoo.conf`:
3. Restart Odoo and install the module from Apps menu.

## Requirements

- Odoo 18
- `account` module (Accounting/Invoicing)
- A bank journal configured in Odoo (M-Pesa journal recommended)

## Roadmap

- [x] Transaction model and views
- [x] Invoice matching engine
- [x] Automatic payment creation and posting
- [x] Full accounting reconciliation
- [ ] Daraja API integration (pull real M-Pesa transactions)
- [ ] Batch reconciliation
- [ ] Dashboard and reconciliation reports
- [ ] Scheduled auto-reconciliation (cron jobs)

## Author

Built by [Nichokajuju](https://github.com/Nichokajuju) as a portfolio project.

## License

LGPL-3
=======
# odoo-mpesa-auto-reconciler
>>>>>>> 32eea72f199e217811166ad4cf8fad1a71ea1fea
