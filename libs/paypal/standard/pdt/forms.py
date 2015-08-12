#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django

from paypal.standard.forms import PayPalStandardBaseForm
from paypal.standard.pdt.models import PayPalPDT


class PayPalPDTForm(PayPalStandardBaseForm):
    class Meta:
        model = PayPalPDT
        if django.VERSION >= (1, 6):
            fields = '__all__'
