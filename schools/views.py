from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from portals.decorators import role_required
from schools.forms import AcademicTermForm
from schools.models import AcademicTerm

# from portals.decorators import admin_required   # reuse yours
