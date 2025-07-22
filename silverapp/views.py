from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from .forms import *
import random
from decimal import Decimal, InvalidOperation
from .models import *
from django.contrib.auth import logout
from django.db import IntegrityError
from django.utils.crypto import get_random_string
import traceback
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.hashers import check_password  # f
from django.db.models import Q
from django.db import transaction
from django.utils.timezone import now
from .utils import get_browser_os, get_client_ip  
from django.http import HttpResponseNotFound
import user_agents
from datetime import datetime
from django.http import HttpResponse
import os
from django.db.models import ProtectedError

from django.contrib.auth.decorators import login_required

# Create your views here.

def userlogin(request):
    msg = ""

    if request.method == 'POST':
        user_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        print("🔐 Login form submitted with:", user_input, password)

        # === Try login_tbl ===
        user = login_tbl.objects.filter(Q(username__iexact=user_input) | Q(email__iexact=user_input)).first()

        if user:
            print("✅ login_tbl user found:", user.email)

            is_valid = check_password(password, user.password)
            if not is_valid:
                is_valid = user.password == password  # fallback for plain text

            if is_valid:
                if user.is_blocked:
                    msg = "Your account is blocked."
                    print("⛔ Blocked login_tbl user")
                else:
                    # Save session
                    request.session['user'] = user.email
                    request.session['user_type'] = 'Admin User' if user.is_superuser else 'Regular User'
                    request.session['is_superuser'] = user.is_superuser

                    # Determine login info
                    login_type = 'Admin User' if user.is_superuser else 'Regular User'
                    browser, os = get_browser_os(request)
                    ip = get_client_ip(request)

                    # Create login log
                    LoginLog.objects.create(
                        user=user,
                        login_type=login_type,
                        browser=browser,
                        operating_system=os,
                        ip_address=ip
                    )

                    print(f"✅ Logged in: {login_type} - {user.email}")
                    return redirect('subusers')
            else:
                msg = "Invalid password."
                print("❌ Wrong password (login_tbl)")

        else:
            # === Try SubMaster ===
            submaster = SubMaster.objects.filter(login_id__iexact=user_input).first()

            if submaster:
                print("✅ SubMaster found:", submaster.email)

                is_valid = check_password(password, submaster.password)
                if not is_valid:
                    is_valid = submaster.password == password  # fallback

                if is_valid:
                    if submaster.is_blocked:
                        msg = "Your SubMaster account is blocked."
                        print("⛔ Blocked SubMaster user")
                    else:
                        # Save session
                        request.session['user'] = submaster.login_id
                        request.session['user_type'] = 'Sub Master'

                        # Log SubMaster login (set user=None since FK is to login_tbl)
                        browser, os = get_browser_os(request)
                        ip = get_client_ip(request)

                        LoginLog.objects.create(
                            user=None,  # can't set login_tbl user here
                            login_type="Sub Master",
                            browser=browser,
                            operating_system=os,
                            ip_address=ip
                        )

                        print(f"✅ Logged in as SubMaster: {submaster.login_id}")
                        return redirect('submasters')
                else:
                    msg = "Invalid password."
                    print("❌ Wrong password (SubMaster)")
            else:
                msg = "User not found in login_tbl or SubMaster."
                print("❌ User not found in either table")

    return render(request, 'login.html', {'msg': msg})
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login') 
def subusers(request):
    # Check for session user
    email = request.session.get('user')
    print("Email from session:", email)

    if not email:
        return redirect('login')

    # Get the logged-in user
    user = login_tbl.objects.filter(email__iexact=email).first()
    print("User found:", user)

    if not user:
        return redirect('login')

    # Check superuser status
    is_superuser = bool(getattr(user, 'is_superuser', False))
    user_type = 'Admin User' if is_superuser else 'Regular User'
    welcome_message = f"Welcome {user_type}" if is_superuser else ""

    # Fetch all subusers
    data = add_subuser.objects.all()

    context = {
        'cuser': user,
        'data': data,
        'is_superuser': is_superuser,
        'welcome_message': welcome_message,
    }

    return render(request, 'subusers.html', context)

def subuser_add(request):
    SECTIONS = {
        1: "Sub Masters Management",
        2: "Category Management",
        3: "Motor Rating - kW/HP Management",
        4: "Phase Management",
        5: "RPM Management",
        6: "Pipe Size Management",
        7: "Discharge Management",
        8: "Discharge Unit Review",
        9: "Motor Body Material Management",
        10: "Certification Management",
        11: "Motor Rotor Material Management",
        12: "Impeller/Bowl Material Management",
        13: "Motor Type Management",
        14: "Star Rating Management",
        15: "Size Management",
        16: "Product Management",
        17: "Hertz-Hz Management"
    }

    if request.method == "POST":
        try:
            # === Get form data ===
            email = request.POST.get("email")
            login_id = request.POST.get("id")
            new_password = request.POST.get("new_password")
            username_str = request.POST.get("username")
            foldername = request.POST.get("foldername")
            licence_domain = request.POST.get("licence_domain")
            embed_domain = request.POST.get("embed_domain")
            firstname = request.POST.get("firstname")
            lastname = request.POST.get("lastname")
            access_code = request.POST.get("access_code")
            address = request.POST.get("address")
            zipcode = request.POST.get("zipcode")
            mobile = request.POST.get("mobile")
            fax = request.POST.get("fax")
            db_host = request.POST.get("database_host")
            db_username = request.POST.get("db_username")
            db_name = request.POST.get("db_name")
            db_password = request.POST.get("db_password")
            is_blocked = bool(request.POST.get("is_blocked"))

            # === Handle file uploads ===
            licence_logo = request.FILES.get("licence_logo")
            tools_logo = request.FILES.get("tools_logo")
            login_screenlogo = request.FILES.get("login_screenlogo")

            # === Check or create login_tbl user ===
            user_obj, created = login_tbl.objects.get_or_create(
                email=email,
                defaults={
                    'username': username_str,
                    'password': new_password,
                    'firstname': firstname,
                    'lastname': lastname,
                    'is_blocked': is_blocked,
                }
            )
            if not created:
                user_obj.username = username_str
                user_obj.password = new_password
                user_obj.firstname = firstname
                user_obj.lastname = lastname
                user_obj.is_blocked = is_blocked
                user_obj.save()

            # === Create add_subuser ===
            subuser = add_subuser.objects.create(
                username=user_obj,
                new_password=new_password,
                email=email,
                login_id=login_id,
                foldername=foldername,
                licence_domain=licence_domain,
                embed_domain=embed_domain,
                licence_logo=licence_logo,
                tools_logo=tools_logo,
                login_screenlogo=login_screenlogo,
                firstname=firstname,
                lastname=lastname,
                access_code=access_code,
                address=address,
                zipcode=zipcode,
                mobile=mobile,
                fax=fax,
                database_host=db_host,
                db_username=db_username,
                db_name=db_name,
                db_password=db_password,
                is_blocked=is_blocked,
            )

            # === Save SubUser Permissions ===
            for i in SECTIONS.keys():
                allowed_str = request.POST.get(f'allowed_{i}', '0')
                try:
                    allowed = int(allowed_str)
                except ValueError:
                    allowed = 0

                unlimited = 'unlimited_%d' % i in request.POST
                enabled = 'enabled_%d' % i in request.POST

                SubUserPermission.objects.create(
                    user=user_obj,
                    section_name=SECTIONS[i],
                    allowed=allowed,
                    unlimited=unlimited,
                    enabled=enabled
    )

            messages.success(request, "Subuser added successfully.")
            return redirect("subusers")

        except Exception as e:
            print("Error while adding subuser:", e)
            messages.error(request, f"Error: {str(e)}")

    return render(request, "add_subusers.html", {"sections": SECTIONS})

def forgot(request):
    if request.method == 'GET':
    
        captcha = str(random.randint(1111, 9999))
        request.session['captcha'] = captcha

    elif request.method == 'POST':
        username = request.POST.get('username')
        entered_captcha = request.POST.get('captcha')
        stored_captcha = request.session.get('captcha')

        if entered_captcha == stored_captcha:
            print("Captcha matched.")
            user = login_tbl.objects.filter(username=username).first()
            if user:
                request.session['username'] = username
                return redirect("/changepass")  
            else:
                print("User not found.")
                captcha = str(random.randint(1111, 9999))
                request.session['captcha'] = captcha
               
        else:
            print("Captcha mismatch.")
       
            captcha = str(random.randint(1111, 9999))
            request.session['captcha'] = captcha

    return render(request,'forgotpass.html',{'captcha':captcha})
def change_pass(request):
    if request.method=='POST':
        newpass=passForm(request.POST)
        password=request.session.get('password')
        user = login_tbl.objects.filter(password=password).first()
        if newpass.is_valid():
            newpass=passForm(request.POST,instance=user)
            newpass.save()
            print("success")
            return redirect('/')
        else:
            print(newpass.errors)
    return render(request,'changepass.html')


# Define all your section keys and names
def edit_subusers(request, id):
    subuser_instance = get_object_or_404(add_subuser, id=id)
    login_instance = subuser_instance.username  # FK to login_tbl

    SECTIONS = {
        1: "Sub Masters Management",
        2: "Category Management",
        3: "Motor Rating - kW/HP Management",
        4: "Phase Management",
        5: "RPM Management",
        6: "Pipe Size Management",
        7: "Discharge Management",
        8: "Discharge Unit Review",
        9: "Motor Body Material Management",
        10: "Certification Management",
        11: "Motor Rotor Material Management",
        12: "Impeller/Bowl Material Management",
        13: "Motor Type Management",
        14: "Star Rating Management",
        15: "Size Management",
        16: "Product Management",
        17: "Hertz-Hz Management"
    }

    if request.method == 'POST':
        form = addsubuserForm(request.POST, request.FILES, instance=subuser_instance)

        if form.is_valid():
            subuser = form.save(commit=False)

            # Update login_tbl fields
            login_instance.email = request.POST.get("email", login_instance.email)
            login_instance.firstname = request.POST.get("firstname", login_instance.firstname)
            login_instance.lastname = request.POST.get("lastname", login_instance.lastname)
            login_instance.save()

            # Update subuser custom fields
            subuser.new_password = request.POST.get("new_password", subuser.new_password)
            subuser.foldername = request.POST.get("foldername", subuser.foldername)
            subuser.licence_domain = request.POST.get("licence_domain", subuser.licence_domain)
            subuser.embed_domain = request.POST.get("embed_domain", subuser.embed_domain)
            subuser.access_code = request.POST.get("access_code", subuser.access_code)
            subuser.address = request.POST.get("address", subuser.address)
            subuser.zipcode = request.POST.get("zipcode", subuser.zipcode)
            subuser.mobile = request.POST.get("mobile", subuser.mobile)
            subuser.fax = request.POST.get("fax", subuser.fax)
            subuser.login_id = request.POST.get("login_id", subuser.login_id)

            # Handle logos
            if 'licence_logo' in request.FILES:
                subuser.licence_logo = request.FILES['licence_logo']
            if 'tools_logo' in request.FILES:
                subuser.tools_logo = request.FILES['tools_logo']
            if 'login_screenlogo' in request.FILES:
                subuser.login_screenlogo = request.FILES['login_screenlogo']

            # Block status
            subuser.is_blocked = 'is_blocked' in request.POST

            subuser.save()

            # Update subuser permissions
            for sec_id, section_name in SECTIONS.items():
                allowed = int(request.POST.get(f'allowed_{sec_id}', 0))
                unlimited = request.POST.get(f'unlimited_{sec_id}') == 'on'
                enabled = request.POST.get(f'enabled_{sec_id}') == 'on'

                permission, created = SubUserPermission.objects.get_or_create(
                    user=login_instance,
                    section_name=section_name,
                    defaults={
                        'allowed': allowed,
                        'unlimited': unlimited,
                        'enabled': enabled
                    }
                )
                if not created:
                    permission.allowed = allowed
                    permission.unlimited = unlimited
                    permission.enabled = enabled
                    permission.save()

            messages.success(request, "Subuser and permissions updated successfully.")
            return redirect('subusers')
        else:
            messages.error(request, "Form is invalid. Please check and try again.")
    else:
        form = addsubuserForm(instance=subuser_instance)

    permissions = SubUserPermission.objects.filter(user=login_instance)
    existing_permissions = {
        perm.section_name: {
            'allowed': perm.allowed,
            'unlimited': perm.unlimited,
            'enabled': perm.enabled
        }
        for perm in permissions
    }

    return render(request, 'edit_subusers.html', {
        'form': form,
        'user_instance': subuser_instance,
        'sections': SECTIONS.items(),
        'existing_permissions': existing_permissions,
    })


def view_subusers(request, id=None):
    cuser = request.session.get('user')

    SECTIONS = {
        1: "Sub Masters Management",
        2: "Category Management",
        3: "Motor Rating - kW/HP Management",
        4: "Phase Management",
        5: "RPM Management",
        6: "Pipe Size Management",
        7: "Discharge Management",
        8: "Discharge Unit Review",
        9: "Motor Body Material Management",
        10: "Certification Management",
        11: "Motor Rotor Material Management",
        12: "Impeller/Bowl Material Management",
        13: "Motor Type Management",
        14: "Star Rating Management",
        15: "Size Management",
        16: "Product Management",
        17: "Hertz-Hz Management"
    }

    if id:
        user = get_object_or_404(add_subuser, id=id)
        login_instance = user.username  # This is the FK to login_tbl

        # Get permissions of this sub-user
        permissions = SubUserPermission.objects.filter(user=login_instance)
        existing_permissions = {
            perm.section_name: {
                'allowed': perm.allowed,
                'unlimited': perm.unlimited,
                'enabled': perm.enabled
            }
            for perm in permissions
        }

        return render(request, 'view_subusers.html', {
            'cuser': cuser,
            'data': [user],  # Wrapped in a list for template loop
            'login_user': login_instance,
            'sections': SECTIONS.items(),
            'existing_permissions': existing_permissions
        })

    # No ID provided — list all subusers
    data = add_subuser.objects.all()
    return render(request, 'view_subusers.html', {
        'cuser': cuser,
        'data': data,
        'sections': SECTIONS.items(),
        'existing_permissions': {}
    })
def dashboard(request):
    return render(request,'dashboard.html')
def deletedata(request,id):
    stid=add_subuser.objects.get(id=id)
    add_subuser.delete(stid)
    return redirect('subusers')
def submasters(request):
    email = request.session.get('user')
    print("Email from session:", email)

    if not email:
        return redirect('login')

    # Get the logged-in user
    user = login_tbl.objects.filter(email__iexact=email).first()
    print("User found:", user)

    if not user:
        return redirect('login')

    # Check superuser status
    is_superuser = getattr(user, 'is_superuser', False)
    user_type = 'Admin User' if is_superuser else 'Regular User'
    welcome_message = f"Welcome {user_type}" if is_superuser else ""

    # Fetch only Sub Masters from separate table
    data = SubMaster.objects.all()

    context = {
        'cuser': user,
        'data': data,
        'is_superuser': is_superuser,
        'welcome_message': welcome_message,
    }

    return render(request, 'submasters.html', context)

def add_submasters(request):
    SECTIONS = {
        1: "Sub Masters Management",
        2: "Category Management",
        3: "Motor Rating - kW/HP Management",
        4: "Phase Management",
        5: "RPM Management",
        6: "Pipe Size Management",
        7: "Discharge Management",
        8: "Discharge Unit Review",
        9: "Motor Body Material Management",
        10: "Certification Management",
        11: "Motor Rotor Material Management",
        12: "Impeller/Bowl Material Management",
        13: "Motor Type Management",
        14: "Star Rating Management",
        15: "Size Management",
        16: "Product Management",
        17: "Hertz-Hz Management"
    }

    if request.method == "POST":
        try:
            # 1. Get form data
            login_id = request.POST.get("login_id", "").strip()
            email = request.POST.get("email", "").strip()
            password = request.POST.get("password", "").strip()
            firstname = request.POST.get("firstname", "")
            lastname = request.POST.get("lastname", "")
            is_blocked = bool(request.POST.get("is_blocked"))

            foldername = request.POST.get("foldername", "")
            licence_domain = request.POST.get("licence_domain", "")
            embed_domain = request.POST.get("embed_domain", "")
            access_code = request.POST.get("access_code", "")
            address = request.POST.get("address", "")
            zipcode = request.POST.get("zipcode", "")
            mobile = request.POST.get("mobile", "")
            fax = request.POST.get("fax", "")
            database_host = request.POST.get("database_host", "")
            db_username = request.POST.get("db_username", "")
            db_name = request.POST.get("db_name", "")
            db_password = request.POST.get("db_password", "")

            licence_logo = request.FILES.get("licence_logo")
            tools_logo = request.FILES.get("tools_logo")
            login_screenlogo = request.FILES.get("login_screenlogo")

            print(f"📥 Received: {login_id} {email} {password}")

            # 2. Create or fetch login_tbl user
            user_obj, created = login_tbl.objects.get_or_create(
                email=email,
                defaults={
                    'username': login_id,
                    'password': password,
                    'firstname': firstname,
                    'lastname': lastname,
                    'is_blocked': is_blocked,
                }
            )

            if not created:
                # User already exists, update it
                user_obj.username = login_id
                user_obj.password = password
                user_obj.firstname = firstname
                user_obj.lastname = lastname
                user_obj.is_blocked = is_blocked
                user_obj.save()

            # 3. Create SubMaster
            SubMaster.objects.create(
                login_id=login_id,
                password=password,
                firstname=firstname,
                lastname=lastname,
                email=email,
                is_blocked=is_blocked,
                foldername=foldername,
                licence_domain=licence_domain,
                embed_domain=embed_domain,
                access_code=access_code,
                address=address,
                zipcode=zipcode,
                mobile=mobile,
                fax=fax,
                database_host=database_host,
                db_username=db_username,
                db_name=db_name,
                db_password=db_password,
                licence_logo=licence_logo,
                tools_logo=tools_logo,
                login_screenlogo=login_screenlogo,
                user=user_obj
            )

            # 4. Save SubMaster Permissions
            for i, section in SECTIONS.items():
                allowed = int(request.POST.get(f"allowed_{i}", 0) or 0)
                unlimited = f"unlimited_{i}" in request.POST
                enabled = f"enabled_{i}" in request.POST

                SubmasterPermission.objects.create(
                    user=user_obj,
                    section_name=section,
                    allowed=allowed,
                    unlimited=unlimited,
                    enabled=enabled
                )

            messages.success(request, "SubMaster added successfully.")
            return redirect("submasters")

        except Exception as e:
            print("❌ Error while adding SubMaster:", e)
            messages.error(request, f"Error while adding SubMaster: {e}")

    return render(request, "add_submasters.html", {"sections": SECTIONS})
SECTIONS = {
    1: "Sub Masters Management",
    2: "Category Management",
    3: "Motor Rating - kW/HP Management",
    4: "Phase Management",
    5: "RPM Management",
    6: "Pipe Size Management",
    7: "Discharge Management",
    8: "Discharge Unit Review",
    9: "Motor Body Material Management",
    10: "Certification Management",
    11: "Motor Rotor Material Management",
    12: "Impeller/Bowl Material Management",
    13: "Motor Type Management",
    14: "Star Rating Management",
    15: "Size Management",
    16: "Product Management",
    17: "Hertz-Hz Management"
}

 

def edit_submasters(request, id):
    submaster = get_object_or_404(SubMaster, id=id)

    # Get login_tbl user for permissions
    try:
        login_user = login_tbl.objects.get(username=submaster.login_id)
    except login_tbl.DoesNotExist:
        login_user = None

    if request.method == "POST":
        submaster.login_id = request.POST.get("login_id", submaster.login_id)
        submaster.password = request.POST.get("password", submaster.password)
        submaster.firstname = request.POST.get("firstname", submaster.firstname)
        submaster.lastname = request.POST.get("lastname", submaster.lastname)
        submaster.email = request.POST.get("email", submaster.email)
        submaster.is_blocked = bool(request.POST.get("is_blocked"))

        submaster.foldername = request.POST.get("foldername", submaster.foldername)
        submaster.licence_domain = request.POST.get("licence_domain", submaster.licence_domain)
        submaster.embed_domain = request.POST.get("embed_domain", submaster.embed_domain)
        submaster.access_code = request.POST.get("access_code", submaster.access_code)
        submaster.address = request.POST.get("address", submaster.address)
        submaster.zipcode = request.POST.get("zipcode", submaster.zipcode)
        submaster.mobile = request.POST.get("mobile", submaster.mobile)
        submaster.fax = request.POST.get("fax", submaster.fax)

        submaster.database_host = request.POST.get("database_host", submaster.database_host)
        submaster.db_username = request.POST.get("db_username", submaster.db_username)
        submaster.db_name = request.POST.get("db_name", submaster.db_name)
        submaster.db_password = request.POST.get("db_password", submaster.db_password)

        if 'licence_logo' in request.FILES:
            submaster.licence_logo = request.FILES['licence_logo']
        if 'tools_logo' in request.FILES:
            submaster.tools_logo = request.FILES['tools_logo']
        if 'login_screenlogo' in request.FILES:
            submaster.login_screenlogo = request.FILES['login_screenlogo']

        submaster.save()

        # Save/update login_tbl data
        if login_user:
            login_user.username = submaster.login_id
            login_user.email = submaster.email
            login_user.password = submaster.password
            login_user.firstname = submaster.firstname
            login_user.lastname = submaster.lastname
            login_user.is_blocked = submaster.is_blocked
            login_user.save()
        else:
            login_user = login_tbl.objects.create(
                username=submaster.login_id,
                email=submaster.email,
                password=submaster.password,
                firstname=submaster.firstname,
                lastname=submaster.lastname,
                is_blocked=submaster.is_blocked
            )

        # Update permissions
        for sec_id, section in SECTIONS.items():
            allowed = int(request.POST.get(f"allowed_{sec_id}", 0))
            unlimited = request.POST.get(f"unlimited_{sec_id}") == 'on'
            enabled = request.POST.get(f"enabled_{sec_id}") == 'on'

            perm, created = SubmasterPermission.objects.get_or_create(
                user=login_user,
                section_name=section,
                defaults={
                    'allowed': allowed,
                    'unlimited': unlimited,
                    'enabled': enabled
                }
            )
            if not created:
                perm.allowed = allowed
                perm.unlimited = unlimited
                perm.enabled = enabled
                perm.save()

        messages.success(request, "SubMaster and permissions updated successfully.")
        return redirect("submasters")

    # Existing permissions dict
    permissions = SubmasterPermission.objects.filter(user=login_user)
    existing_permissions = {
        perm.section_name: {
            'allowed': perm.allowed,
            'unlimited': perm.unlimited,
            'enabled': perm.enabled
        } for perm in permissions
    }

    return render(request, "edit_submasters.html", {
        "submaster": submaster,
        "sections": SECTIONS.items(),
        "existing_permissions": existing_permissions,
    })
def view_submasters(request, id=None):
    cuser = request.session.get('user')

    SECTIONS = {
        1: "Sub Masters Management",
        2: "Category Management",
        3: "Motor Rating - kW/HP Management",
        4: "Phase Management",
        5: "RPM Management",
        6: "Pipe Size Management",
        7: "Discharge Management",
        8: "Discharge Unit Review",
        9: "Motor Body Material Management",
        10: "Certification Management",
        11: "Motor Rotor Material Management",
        12: "Impeller/Bowl Material Management",
        13: "Motor Type Management",
        14: "Star Rating Management",
        15: "Size Management",
        16: "Product Management",
        17: "Hertz-Hz Management"
    }

    if id:
        submaster = get_object_or_404(SubMaster, id=id)
        login_user = login_tbl.objects.filter(username=submaster.login_id).first()

        permissions = SubmasterPermission.objects.filter(user=login_user)
        existing_permissions = {
            perm.section_name: {
                'allowed': perm.allowed,
                'unlimited': perm.unlimited,
                'enabled': perm.enabled
            }
            for perm in permissions
        }

        return render(request, 'view_submasters.html', {
            'cuser': cuser,
            'data': [submaster],  # So you can reuse template loop
            'login_user': login_user,
            'sections': SECTIONS.items(),
            'existing_permissions': existing_permissions
        })

    # List all submasters if no ID provided
    all_submasters = SubMaster.objects.all()
    return render(request, 'view_submasters.html', {
        'cuser': cuser,
        'data': all_submasters,
        'sections': SECTIONS.items(),
        'existing_permissions': {}
    })
def login_log(request):
    if 'user' not in request.session:
        return redirect('login')

    logs = LoginLog.objects.all().order_by('-id')

    # Get filter values
    login_type_filter = request.GET.get('login_type')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Filter by login type
    if login_type_filter:
        logs = logs.filter(login_type__icontains=login_type_filter)

    # Filter by from_date
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            logs = logs.filter(login_time__date__gte=from_date_obj)
        except ValueError:
            pass

    # Filter by to_date
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            logs = logs.filter(login_time__date__lte=to_date_obj)
        except ValueError:
            pass

    return render(request, 'login_log.html', {
        'logs': logs,
        'login_type_filter': login_type_filter,
        'from_date': from_date,
        'to_date': to_date,
    })
def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')

def get_browser_os(request):
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = user_agents.parse(ua_string)
    browser = f"{user_agent.browser.family} {user_agent.browser.version_string}"
    os = f"{user_agent.os.family} {user_agent.os.version_string}"
    return browser, os
def settings_silver(request):
    # Get or create the singleton settings object
    setting, created = SystemSetting.objects.get_or_create(id=1)

    if request.method == 'POST':
        setting.no_star_message = request.POST.get('no_star_message', '')
        setting.head_unit = request.POST.get('head_unit', '')
        setting.discharge_unit = request.POST.get('discharge_unit', '')
        setting.rating_unit = request.POST.get('rating_unit', '')
        setting.per_page = request.POST.get('per_page', '10')
        setting.help_head = request.POST.get('help_head', '')
        setting.save()

        messages.success(request, "System settings updated successfully.")
        return redirect('subusers')  # URL name

    context = {
        'no_star_message': setting.no_star_message,
        'head_unit': setting.head_unit,
        'discharge_unit': setting.discharge_unit,
        'rating_unit': setting.rating_unit,
        'per_page': setting.per_page,
        'help_head': setting.help_head,
    }

    return render(request,'settings_silver.html', context)
def delete_submaster(request, id):
    if not request.session.get('user'):  # Ensure user is logged in
        return redirect('login')  # Adjust this as per your login route

    submaster = get_object_or_404(SubMaster, id=id)
    submaster.delete()
    messages.success(request, "SubMaster deleted successfully.")
    return redirect('submasters')  # Adjust this to your list view name
def category_list(request):
    from .models import Category, CategoryMasterLink

    categories = Category.objects.all()
    category_data = []

    for cat in categories:
        applicable_areas = CategoryMasterLink.objects.filter(
            category=cat, is_applicable=True
        ).values_list('master_area', flat=True)

        category_data.append({
            'id': cat.id,
            'name': cat.name,
            'account': cat.account,
            'is_active': cat.is_active,
            'applicable_areas': list(applicable_areas),
            'image': cat.image.url if cat.image else None  # ✅ include image URL
        })

    return render(request, 'categories.html', {'categories': category_data})
def delete_categories(request, id):
    category = get_object_or_404(Category, id=id)
    category.delete()
    return redirect('categories')
def add_category(request):
    master_areas = [
        "Motor Rating (kW/HP)", "Phase", "Hertz - Hz", "RPM",
        "Motor Body Material", "Motor Rotor Material", "Pipe Size",
        "Size", "Certifications", "Star Rating",
        "Impeller/Bowl Material", "Motor Type", "Discharge"
    ]

    if request.method == 'POST':
        name = request.POST.get('category_name')
        account = request.POST.get('account')
        discharge_unit = request.POST.get('discharge_unit')
        is_active = request.POST.get('status') == 'on'
        image_file = request.FILES.get('category_image')

        if name and account and image_file:
            category = Category.objects.create(
                name=name,
                account=account,
                discharge_unit=discharge_unit,
                is_active=is_active,
                image=image_file
            )

            for i, area in enumerate(master_areas, start=1):
                is_checked = request.POST.get(f'applicable_{i}') == 'on'
                CategoryMasterLink.objects.create(
                    category=category,
                    master_area=area,
                    is_applicable=is_checked
                )

            return redirect('categories')

    return render(request, 'add_category.html', {
        'master_areas': list(enumerate(master_areas, start=1))
    })

def edit_category(request, id):
    master_areas = [
        "Motor Rating (kW/HP)", "Phase", "Hertz - Hz", "RPM",
        "Motor Body Material", "Motor Rotor Material", "Pipe Size",
        "Size", "Certifications", "Star Rating",
        "Impeller/Bowl Material", "Motor Type", "Discharge"
    ]

    category = get_object_or_404(Category, id=id)
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)

    if request.method == 'POST':
        if form.is_valid():
            # Save form and get updated category instance
            category = form.save()

            # Clear old master links
            CategoryMasterLink.objects.filter(category=category).delete()

            # Save new master links
            for i, area in enumerate(master_areas, start=1):
                checkbox_name = f'applicable_{i}'
                is_checked = request.POST.get(checkbox_name) == 'on'
                CategoryMasterLink.objects.create(
                    category=category,
                    master_area=area,
                    is_applicable=is_checked
                )

            # ✅ Successful update — redirect
            return redirect('categories')  # make sure your URL name is 'categories'

    # Get selected areas for checkbox prefill
    selected_areas = CategoryMasterLink.objects.filter(
        category=category, is_applicable=True
    ).values_list('master_area', flat=True)

    return render(request, 'edit_category.html', {
        'form': form,
        'category': category,
        'master_areas': list(enumerate(master_areas, start=1)),
        'selected_areas': list(selected_areas),
    })


def motor_rating(request):
    query = request.GET.get('filter')
    motors = MotorRating.objects.all()

    if query:
        try:
            # Convert to Decimal safely
            query_decimal = Decimal(query.strip())

            # Match exactly against kw or hp
            motors = motors.filter(Q(kw=query_decimal) | Q(hp=query_decimal))
        except InvalidOperation:
            # If query isn't a valid number, ignore it
            motors = MotorRating.objects.none()

    return render(request, 'motor_rating.html', {
        'motors': motors,
        'filter_query': query
    })

def add_motor(request):
    if request.method == 'POST':
        form = MotorRatingForm(request.POST)
        if form.is_valid():
            form.save()
            print("✅ Saved successfully!")
            return redirect('motor_rating')
        else:
            print("❌ Form errors:", form.errors)
    else:
        form = MotorRatingForm(initial={'status': True})
    return render(request, 'add_motor.html', {'form': form})
def edit_motor(request,id):
    motor = get_object_or_404(MotorRating, id=id)

    if request.method == 'POST':
        kw = request.POST.get('kw')
        hp = request.POST.get('hp')
        status = request.POST.get('status') == 'on'  # checkbox

        motor.kw = kw
        motor.hp = hp
        motor.status = status
        motor.save()

        return redirect('motor_rating')  # redirect back to listing

    return render(request, 'edit_motor.html', {'motor': motor})
def delete_single_motor(request,id):
    motor = get_object_or_404(MotorRating, id=id)
    if request.method == 'POST':
        motor.delete()
    return redirect('motor_rating')
def phase(request):
    filter_query = request.GET.get('filter', '')
    phases = Phase.objects.all()
    
    if filter_query:
        phases = phases.filter(name__icontains=filter_query)

    return render(request, 'phase.html', {
        'phases': phases,
        'filter_query': filter_query
    })
def add_phase(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        short_name = request.POST.get('short_name')
        account = request.POST.get('account', 'Pump Demo')  # Default value if none provided
        status = True if request.POST.get('status') == 'on' else False

        # Save to database
        Phase.objects.create(
            name=name,
            short_name=short_name,
            account=account,
            status=status
        )

        return redirect('phase')  # Replace with your list view name

    return render(request, 'add_phase.html')
def edit_phase(request, id):
    phase = get_object_or_404(Phase, id=id)
    accounts = Phase.objects.all()

    if request.method == 'POST':
        phase.name = request.POST.get('name')
        phase.short_name = request.POST.get('short_name')
        phase.account_id = request.POST.get('account')  # Assuming this is a ForeignKey
        phase.status = bool(request.POST.get('status'))  # Checkbox returns 'on' or nothing
        phase.save()
        return redirect('phase')  # Redirect back to the phase list page

    return render(request, 'edit_phase.html', {
        'phase': phase,
        'accounts': accounts,
    })
def delete_phase(request, id):
    phase = get_object_or_404(Phase, id=id)
    phase.delete()
    return redirect('phase')  # Replace 'phase' with your listing page's URL name

def hertz(request):
    query = request.GET.get('filter', '').strip()  # Match the form field name
    if query:
        hertz_items = Hertz.objects.filter(Q(hz_name__icontains=query))
    else:
        hertz_items = Hertz.objects.all()

    context = {
        'hertz_items': hertz_items,
        'query': query,
    }
    return render(request, 'hertz.html', context)

def add_hertz(request):
    if request.method == 'POST':
        hz_name = request.POST.get('hz_name')
        account = request.POST.get('account', 'Pump Demo')  # default value
        status = True if request.POST.get('status') == 'on' else False

        # Save to database
        Hertz.objects.create(
            hz_name=hz_name,
            account=account,
            is_active=status
        )

        return redirect('hertz')  # Replace with your correct list view name

    return render(request, 'add_hertz.html')
def edit_hertz(request, id):
    try:
        hertz = Hertz.objects.get(id=id)
    except Hertz.DoesNotExist:
        return redirect('hertz')  # Or show 404 page

    if request.method == 'POST':
        hz_name = request.POST.get('hz_name')
        account = request.POST.get('account', 'Pump Demo')
        status = True if request.POST.get('status') == 'on' else False

        # Update instance
        hertz.hz_name = hz_name
        hertz.account = account
        hertz.is_active = status
        hertz.save()

        return redirect('hertz')

    return render(request, 'edit_hertz.html', {'hertz': hertz})
def delete_single_hertz(request, id):
    Hertz.objects.filter(id=id).delete()
    return redirect('hertz')

def rpm(request):
    query = request.GET.get('filter', '').strip()

    if query:
        rpm_items = RPM.objects.filter(rpm_name__icontains=query)
    else:
        rpm_items = RPM.objects.all()

    return render(request, 'rpm.html', {
        'rpm_items': rpm_items,
        'query': query,
    })

def add_rpm(request):
    if request.method == 'POST':
        rpm_name = request.POST.get('rpm_name')
        account = request.POST.get('account', 'Pump Demo')  # default
        status = True if request.POST.get('status') == 'on' else False

        RPM.objects.create(
            rpm_name=rpm_name,
            account=account,
            is_active=status
        )

        return redirect('rpm')  # use your correct list view name

    return render(request, 'add_rpm.html')
def edit_rpm(request, id):
    rpm = get_object_or_404(RPM, id=id)  # get the instance

    if request.method == 'POST':
        rpm_name = request.POST.get('rpm_name')
        account = request.POST.get('account', 'Pump Demo')
        status = True if request.POST.get('status') == 'on' else False

        rpm.rpm_name = rpm_name
        rpm.account = account
        rpm.is_active = status
        rpm.save()

        return redirect('rpm')

    return render(request, 'edit_rpm.html', {'rpm': rpm})
def delete_single_rpm(request,id):
    if request.method == "POST":
        rpm = get_object_or_404(RPM, id=id)
        rpm.delete()
    return redirect('rpm')
def pipesize(request):
    query = request.GET.get('filter', '').strip()
    pipesizes = PipeSize.objects.prefetch_related('categories')

    if query:
        pipesizes = pipesizes.filter(pipe_size__icontains=query)

    return render(request, 'pipesize.html', {
        'pipesizes': pipesizes,
        'query': query,
    })

def add_pipesize(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        pipe_size = request.POST.get('pipe_size')
        account = request.POST.get('account')
        status = request.POST.get('status') == '1'
        category_ids = request.POST.getlist('categories')  # ✅ FIXED here

        if pipe_size:
            pipe = PipeSize.objects.create(
                pipe_size=pipe_size,
                account=account,
                status=status
            )
            if category_ids:
                pipe.categories.set(category_ids)  # ✅ saves ManyToMany

            return redirect('pipesize')

    return render(request, 'add_pipesize.html', {'categories': categories})
def edit_pipesize(request, id):
    pipe = get_object_or_404(PipeSize, id=id)
    categories = Category.objects.all()

    if request.method == 'POST':
        pipe_size = request.POST.get('pipe_size')
        account = request.POST.get('account')
        status = request.POST.get('status') == '1'
        category_ids = request.POST.getlist('categories')  # no []

        if pipe_size:
            pipe.pipe_size = pipe_size
            pipe.account = account
            pipe.status = status
            pipe.save()

            # ✅ Update ManyToMany
            pipe.categories.set(category_ids)

            return redirect('pipesize')

    return render(request, 'edit_pipesize.html', {
        'pipe': pipe,
        'categories': categories,
        'selected_categories': pipe.categories.values_list('id', flat=True)
    })
def delete_pipesize(request, id):
    pipe = get_object_or_404(PipeSize, id=id)
    if request.method == 'POST':
        try:
            pipe.delete()
        except IntegrityError as e:
            # Show the error for debugging
            return HttpResponse(f"Error deleting: {str(e)}")
    return redirect('pipesize')
def size(request):
    query = request.GET.get('filter', '').strip()
    sizes = Size.objects.prefetch_related('pipe_sizes')

    if query:
        sizes = sizes.filter(star_rating__icontains=query)  # Adjust if your field name is different

    return render(request, 'size.html', {
        'sizes': sizes,
        'query': query,
    })
def add_size(request):
    if request.method == 'POST':
        star_rating = request.POST.get('star_rating')
        account = request.POST.get('account')
        selected_pipe_ids = request.POST.getlist('pipe_sizes[]')  # This is what must come from JS
        status = request.POST.get('status') == 'on'

        print("PIPE IDS:", selected_pipe_ids)  # Debug

        size_obj = Size.objects.create(
            star_rating=star_rating,
            account=account,
            status=status
        )

        if selected_pipe_ids:
            size_obj.pipe_sizes.set(selected_pipe_ids)

        return redirect('size')

    pipe_sizes = list(PipeSize.objects.filter(status=True).values('id', 'pipe_size'))
    return render(request, 'add_size.html', {'pipe_sizes': pipe_sizes})

def edit_size(request, id):
    size = get_object_or_404(Size, id=id)

    if request.method == 'POST':
        size.star_rating = request.POST.get('star_rating')
        size.account = request.POST.get('account')
        size.status = request.POST.get('status') == 'on'
        size.save()

        selected_pipe_ids = request.POST.getlist('pipe_sizes[]')
        size.pipe_sizes.set(selected_pipe_ids)

        return redirect('size')

    pipe_sizes = list(PipeSize.objects.filter(status=True).values('id', 'pipe_size'))
    selected_pipe_ids = list(size.pipe_sizes.values_list('id', flat=True))
    return render(request, 'edit_size.html', {
        'size': size,
        'pipe_sizes': pipe_sizes,
        'selected_pipe_ids': selected_pipe_ids
    })

def delete_size(request, id):
    size = get_object_or_404(Size, id=id)
    if request.method == 'POST':
        try:
            size.delete()
        except IntegrityError as e:
            # Show the error for debugging
            return HttpResponse(f"Error deleting: {str(e)}")
    return redirect('size')  # Replace 'size_list' with your view name for listing sizes
def discharge_unit(request):
    # load from session or initialize
    if 'static_units' not in request.session:
        request.session['static_units'] = {
            1: {'unit': 'M3/HR', 'denotes': 'METER CUBE PER HOUR', 'decimal_places': 1, 'account': 'Pump Demo', 'is_active': True},
            2: {'unit': 'LPS', 'denotes': 'Liter Per Second', 'decimal_places': 4, 'account': 'Pump Demo', 'is_active': True},
            3: {'unit': 'LPH', 'denotes': 'Liter Per Hour', 'decimal_places': 0, 'account': 'Pump Demo', 'is_active': True},
            4: {'unit': 'LPM', 'denotes': 'Liter Per Minute', 'decimal_places': 0, 'account': 'Pump Demo', 'is_active': True},
        }

    units = request.session['static_units']
    return render(request, 'discharge_unit.html', {'units': units})
def edit_discharge_unit(request, id):
    units = request.session.get('static_units', {})

    discharge_unit = units.get(str(id)) or units.get(int(id))  # handle str/int keys

    if not discharge_unit:
        return HttpResponseNotFound("No DischargeUnit matches the given id.")

    if request.method == 'POST':
        discharge_unit['unit'] = request.POST.get('unit')
        discharge_unit['denotes'] = request.POST.get('denotes')
        discharge_unit['decimal_places'] = int(request.POST.get('decimal_places') or 0)
        discharge_unit['account'] = request.POST.get('account')
        discharge_unit['is_active'] = True if request.POST.get('is_active') == 'on' else False
        
        # update session
        units[str(id)] = discharge_unit
        request.session['static_units'] = units

        messages.success(request, "Discharge Unit updated successfully.")
        return redirect('discharge_unit')

    return render(request, 'edit_discharge_unit.html', {'discharge_unit': discharge_unit})
def discharge(request):
    query = request.GET.get('search', '')
    discharges = Discharge.objects.all()

    if query:
        discharges = discharges.filter(discharge__icontains=query)

    return render(request, 'discharge.html', {'discharges': discharges, 'query': query})
def add_discharge(request):
    default_account = "Pump Demo"

    if request.method == 'POST':
        discharge_value = request.POST.get('discharge')
        account_value = request.POST.get('account')

        # ✅ Correct checkbox handling
        is_active = True if 'is_active' in request.POST else False

        print("POST DATA:", request.POST)
        print("Evaluated status:", is_active)

        if discharge_value:
            Discharge.objects.create(
                discharge=discharge_value,
                account=account_value,
                is_active=is_active
            )
            return redirect('discharge')  # Replace with your actual view name

    return render(request, 'add_discharge.html', {
        'default_account': default_account
    })



def edit_discharge(request, id):
    discharge_obj = get_object_or_404(Discharge, id=id)
    default_account = "Pump Demo"

    if request.method == 'POST':
        discharge_value = request.POST.get('discharge')
        account_value = request.POST.get('account')
        is_active = True if 'is_active' in request.POST else False

        print("EDIT POST DATA:", request.POST)
        print("Evaluated status:", is_active)

        discharge_obj.discharge = discharge_value
        discharge_obj.account = account_value
        discharge_obj.is_active = is_active
        discharge_obj.save()

        return redirect('discharge')  # Change to your list view name

    return render(request, 'edit_discharge.html', {
        'discharge_obj': discharge_obj,
        'default_account': default_account
    })

def delete_discharge(request, id):
    discharge = get_object_or_404(Discharge, id=id)
    discharge.delete()
    return redirect('discharge')  # Replace with your actual discharge list view name
def motor_body(request):
    query = request.GET.get('q', '')
    if query:
        materials = MotorMaterial.objects.filter(material_name__icontains=query).order_by('-id')
    else:
        materials = MotorMaterial.objects.all()

    return render(request, 'motor_body.html', {
        'materials': materials,
        'query': query
    })
def add_motor_body(request):
    if request.method == 'POST':
        name = request.POST.get('material_name')
        long_name = request.POST.get('long_name')
        account = request.POST.get('account')
        is_active = 'is_active' in request.POST
        category_ids = request.POST.getlist('categories')

        material = MotorMaterial.objects.create(
            material_name=name,
            long_name=long_name,
            account=account,
            is_active=is_active
        )

        if category_ids:
            material.categories.set(category_ids)

        return redirect('motor_body')

    categories = Category.objects.all()
    return render(request, 'add_motor_body.html', {
        'categories': categories
    })

def edit_motor_body(request, id):
    material = get_object_or_404(MotorMaterial, id=id)

    if request.method == 'POST':
        material.material_name = request.POST.get('material_name')
        material.long_name = request.POST.get('long_name')
        material.account = request.POST.get('account')
        material.is_active = 'is_active' in request.POST

        category_ids = request.POST.getlist('categories')
        material.save()  # Save basic info first

        # Update ManyToMany categories
        if category_ids:
            material.categories.set(category_ids)
        else:
            material.categories.clear()

        return redirect('motor_body')  # redirect to your listing page

    categories = Category.objects.all()
    selected_categories = material.categories.values_list('id', flat=True)

    return render(request, 'edit_motor_body.html', {
        'material': material,
        'categories': categories,
        'selected_categories': selected_categories,
    })

def delete_motor_body(request, id):
    print("⚙️ Attempting to delete ID:", id)

    try:
        material = get_object_or_404(MotorMaterial, id=id)
        print("✅ Found Material:", material)

        material.delete()
        messages.success(request, "Motor Material deleted successfully.")
        print("🗑️ Deleted successfully")

    except ProtectedError as e:
        messages.error(request, "Cannot delete this item. It is used elsewhere.")
        print("⛔ ProtectedError:", e)

    except Exception as e:
        messages.error(request, "Error occurred during deletion.")
        print("❌ General Exception:", e)
def certifications(request):
    query = request.GET.get('q', '')
    if query:
        certificates = Certificate.objects.filter(certificate_name__icontains=query)
    else:
        certificates = Certificate.objects.all().order_by('-id')

    return render(request, 'certifications.html', {
        'certificates': certificates,
        'query': query
    })



def add_certifications(request):
    if request.method == 'POST':
        certificate_name = request.POST.get('certificate_name')
        long_name = request.POST.get('long_name')
        account = request.POST.get('account')
        is_active = request.POST.get('is_active') == 'on'

        if certificate_name:
            Certificate.objects.create(
                certificate_name=certificate_name,
                long_name=long_name,
                account=account,
                is_active=is_active
            )
            messages.success(request, "Certificate added successfully.")
            return redirect('certifications')
        else:
            messages.error(request, "Certificate Name is required.")

    return render(request, 'add_certifications.html')
def edit_certifications(request, id):
    certificate = get_object_or_404(Certificate, id=id)

    if request.method == 'POST':
        certificate_name = request.POST.get('certificate_name')
        long_name = request.POST.get('long_name')
        account = request.POST.get('account')
        is_active = request.POST.get('is_active') == 'on'

        if certificate_name:
            certificate.certificate_name = certificate_name
            certificate.long_name = long_name
            certificate.account = account
            certificate.is_active = is_active
            certificate.save()

            messages.success(request, "Certificate updated successfully.")
            return redirect('certifications')
        else:
            messages.error(request, "Certificate Name is required.")

    return render(request, 'edit_certifications.html', {'certificate': certificate})

def delete_certifications(request, id):
    if request.method == 'POST':
        try:
            certificate = get_object_or_404(Certificate, id=id)
            certificate.delete()
            messages.success(request, "Certificate deleted successfully.")
        except Exception as e:
            messages.error(request, f"Error while deleting: {e}")
    else:
        messages.error(request, "Invalid request method.")

    return redirect('certifications')
def motor_rotor_material(request):
    query = request.GET.get('filter', '').strip()  # Match with the form input name
    materials = MotorRotorMaterial.objects.all()

    if query:
        materials = materials.filter(motor_rotor_name__icontains=query)

    return render(request, 'motor_rotor_material.html', {
        'materials': materials,
        'query': query,  # Pass it to template for keeping input value
    })

def add_motor_rotor(request):
    if request.method == 'POST':
        motor_rotor_name = request.POST.get('motor_rotor_name')
        account = request.POST.get('account', 'Pump Demo')
        is_active = request.POST.get('is_active') == 'on'  # checkbox

        if motor_rotor_name:
            MotorRotorMaterial.objects.create(
                motor_rotor_name=motor_rotor_name,
                account=account,
                is_active=is_active
            )
            messages.success(request, "Rotor Material added successfully.")
            return redirect('motor_rotor_material')
        else:
            messages.error(request, "Rotor Material Name is required.")

    return render(request, 'add_motor_rotor.html')


def edit_motor_rotor(request, id):
    material = get_object_or_404(MotorRotorMaterial, id=id)

    if request.method == 'POST':
        motor_rotor_name = request.POST.get('motor_rotor_name')
        account = request.POST.get('account', 'Pump Demo')
        is_active = 'is_active' in request.POST

        # Only update name if actually provided
        if motor_rotor_name:
            material.motor_rotor_name = motor_rotor_name
        material.account = account
        material.is_active = is_active
        material.save()

        messages.success(request, f"{material.motor_rotor_name} updated successfully.")
        return redirect('motor_rotor_material')

    return render(request, 'edit_motor_rotor.html', {'material': material})

def delete_motor_rotor(request, id):
    material = get_object_or_404(MotorRotorMaterial, id=id)
    material.delete()
    messages.success(request, f"{material.motor_rotor_name} deleted successfully.")
    return redirect('motor_rotor_material')
def impeller(request):
    query = request.GET.get('filter', '').strip()  # use 'filter' to match your input's name
    if query:
        materials = ImpellerMaterial.objects.filter(
            impeller_name__icontains=query
        ).prefetch_related('categories').order_by('-id')
    else:
        materials = ImpellerMaterial.objects.prefetch_related('categories').all().order_by('-id')

    return render(request, 'impeller.html', {
        'materials': materials,
        'query': query
    })


def add_impeller(request):
    if request.method == 'POST':
        print("Form Data:", request.POST)
        impeller_name = request.POST.get('impeller_name')
        long_name = request.POST.get('long_name')
        account = request.POST.get('account')  # Usually 'Pump Demo'
        is_active = 'is_active' in request.POST
        category_ids = request.POST.getlist('categories')

        # Create impeller material entry
        impeller = ImpellerMaterial.objects.create(
            impeller_name=impeller_name,
            long_name=long_name,
            account=account,
            is_active=is_active
        )

        # Set categories if any selected
        if category_ids:
            impeller.categories.set(category_ids)

        return redirect('impeller')  # Redirect to impeller list page

    # GET request — show form
    categories = Category.objects.all()
    return render(request, 'add_impeller.html', {
        'categories': categories
    })

def edit_impeller(request, id):
    impeller = get_object_or_404(ImpellerMaterial, id=id)

    if request.method == 'POST':
        impeller.impeller_name = request.POST.get('impeller_name')
        impeller.long_name = request.POST.get('long_name')
        impeller.account = request.POST.get('account')
        impeller.is_active = 'is_active' in request.POST

        selected_categories = request.POST.getlist('categories')
        impeller.save()
        impeller.categories.set(selected_categories)

        return redirect('impeller')

    categories = Category.objects.all()
    selected_categories = impeller.categories.values_list('id', flat=True)

    return render(request, 'edit_impeller.html', {
        'impeller': impeller,
        'categories': categories,
        'selected_categories': selected_categories
    }) 
def delete_impeller(request, id):
    if request.method == 'POST':
        material = get_object_or_404(ImpellerMaterial, id=id)
        material.delete()
        messages.success(request, 'Material deleted successfully.')
    return redirect('impeller')  # Replace with your actual list view name
def motor_type(request):
    query = request.GET.get('q', '').strip()

    if query:
        motor_types = MotorType.objects.filter(
            motor_type_name__icontains=query
        ).prefetch_related('categories').order_by('-id')
    else:
        motor_types = MotorType.objects.prefetch_related('categories').all().order_by('-id')

    return render(request, 'motor_type.html', {
        'motor_types': motor_types,
        'query': query
    })
def add_motor_type(request):
    if request.method == 'POST':
      
        motor_type_name = request.POST.get('motor_type_name')
        account = request.POST.get('account')  # Usually "Pump Demo"
        is_active = 'status' in request.POST  # checkbox for active status
        category_ids = request.POST.getlist('categories')

        # Create motor type entry
        motor_type = MotorType.objects.create(
            motor_type_name=motor_type_name,
            account=account,
            status=is_active
        )

        # Assign categories
        if category_ids:
            motor_type.categories.set(category_ids)

        return redirect('motor_type')  # redirect to motor type list view

    # GET request — show form
    categories = Category.objects.all()
    return render(request, 'add_motor_type.html', {
        'categories': categories
    })

def edit_motor_type(request, id):
    motor_type = get_object_or_404(MotorType, id=id)

    if request.method == 'POST':
        motor_type.motor_type_name = request.POST.get('motor_type_name')
        motor_type.account = request.POST.get('account')
        motor_type.status = 'status' in request.POST
        category_ids = request.POST.getlist('categories')

        motor_type.save()

        if category_ids:
            motor_type.categories.set(category_ids)
        else:
            motor_type.categories.clear()

        return redirect('motor_type')  # Replace with your list view name

    categories = Category.objects.all()
    selected_categories = motor_type.categories.values_list('id', flat=True)

    return render(request, 'edit_motor_type.html', {
        'motor_type': motor_type,
        'categories': categories,
        'selected_categories': selected_categories,
    })

def delete_motor_type(request, id):
    motor = get_object_or_404(MotorType,id=id)
    if request.method == 'POST':
        motor.delete()
    return redirect('motor_type')
def star_rating(request):
    query = request.GET.get('q', '').strip()
    if query:
        ratings = StarRating.objects.filter(star_rating_name__icontains=query).order_by('-id')
    else:
        ratings = StarRating.objects.all().order_by('-id')

    return render(request, 'star_rating.html', {
        'ratings': ratings,
        'query': query
    })
def add_star_rating(request):
    if request.method == 'POST':
        star_rating_name = request.POST.get('star_rating_name')
        account = request.POST.get('account')
        status = 'status' in request.POST  # checkbox handling

        # Save the star rating
        StarRating.objects.create(
            star_rating_name=star_rating_name,
            account=account,
            status=status
        )

        return redirect('star_rating')  # redirect to your listing view

    # GET request — render form
    accounts = ['Pump Demo']  # or fetch dynamically if needed
    return render(request, 'add_star_rating.html', {
        'accounts': accounts
    })
def edit_star_rating(request, id):
    star_rating = get_object_or_404(StarRating, id=id)

    if request.method == 'POST':
        star_rating.star_rating_name = request.POST.get('star_rating_name')
        star_rating.account = request.POST.get('account')
        star_rating.status = 'status' in request.POST
        star_rating.save()

        return redirect('star_rating')  # replace with your actual list view name

    return render(request, 'edit_star_rating.html', {
        'star_rating': star_rating
    })

def delete_star_rating(request,id):
    if request.method == 'POST':
        rating = get_object_or_404(StarRating, id=id)
        rating.delete()
        messages.success(request, 'Star rating deleted successfully.')
    else:
        messages.error(request, 'Invalid request method.')

    return redirect('star_rating')  # Replace with your actual view name
def products(request):
    category_query = request.GET.get('category', '').strip()
    model_query = request.GET.get('model_name', '').strip()

    # ✅ Start with base queryset
    products = Product.objects.all()

    if category_query and model_query:
        products = products.filter(
            Q(categories__name__iexact=category_query) |
            Q(model_name__icontains=model_query)
        )
    elif category_query:
        products = products.filter(categories__name__iexact=category_query)
    elif model_query:
        products = products.filter(model_name__icontains=model_query)

    # ✅ Now apply select_related and prefetch_related
    products = products.select_related("hertz").prefetch_related('categories').distinct()

    all_categories = Category.objects.all().order_by('name')

    context = {
        'products': products,
        'categories': all_categories,
        'selected_category': category_query,
        'model_query': model_query,
    }

    return render(request, 'products.html', context)

def add_product(request):
    categories = Category.objects.all()

    # ✅ Auto-create default discharge units if DB is empty
    if DischargeUnit.objects.count() == 0:
        static_units = [
            {'unit': 'M3/HR', 'denotes': 'METER CUBE PER HOUR', 'decimal_places': 1},
            {'unit': 'LPS', 'denotes': 'Liter Per Second', 'decimal_places': 4},
            {'unit': 'LPH', 'denotes': 'Liter Per Hour', 'decimal_places': 0},
            {'unit': 'LPM', 'denotes': 'Liter Per Minute', 'decimal_places': 0},
        ]
        for data in static_units:
            DischargeUnit.objects.get_or_create(
                unit=data['unit'],
                defaults={
                    'denotes': data['denotes'],
                    'decimal_places': data['decimal_places'],
                    'account': 'Pump Demo',
                    'status': True
                }
            )

    discharge_units = DischargeUnit.objects.filter(is_active=True, account='Pump Demo')
    motor_ratings = MotorRating.objects.all()
    phases = Phase.objects.all()
    rpms = RPM.objects.all()
    pipe_sizes = PipeSize.objects.all()
    discharges = Discharge.objects.all()
    hertzs = Hertz.objects.all()
    

    if request.method == 'POST':
        model_name = request.POST.get('model_name')
        category_ids = list(map(int, request.POST.getlist('categories')))
        unit_id = request.POST.get('unit')
        motor_rating_id = request.POST.get('motor_rating')
        phase_id = request.POST.get('phase')
        hertz_id = request.POST.get('hertz')
        rpm_id = request.POST.get('rpm')
        pipe_size_id = request.POST.get('pipe_size')
        discharge_ids = request.POST.getlist('discharge')
        thumb_image = request.FILES.get('thumb_image')
        preview_image = request.FILES.get('preview_image')
        status = request.POST.get('status') == 'on'

        unit = DischargeUnit.objects.filter(id=unit_id).first()
        motor_rating = MotorRating.objects.filter(id=motor_rating_id).first()
        phase = Phase.objects.filter(id=phase_id).first()
        hertz = Hertz.objects.filter(id=hertz_id).first()
        rpm = RPM.objects.filter(id=rpm_id).first()
        pipe_size = PipeSize.objects.filter(id=pipe_size_id).first()

        product = Product.objects.create(
            model_name=model_name,
            account='Pump Demo',
            unit=unit,
            hertz=hertz,
            motor_rating=motor_rating,
            phase=phase,
            rpm=rpm,
            pipe_size=pipe_size,
            thumb_image=thumb_image,
            preview_image=preview_image,
            status=status
        )

        if category_ids:
            product.categories.set(category_ids)
        if discharge_ids:
            product.discharges.set(discharge_ids)

        # ✅ Handle MotorPumpData entries
        discharges_data = request.POST.getlist("discharge[]")
        heads = request.POST.getlist("head[]")
        recommends = request.POST.getlist("recommend[]")
        motor_ratings_data = request.POST.getlist("data_motor_rating[]")
        pipe_sizes_data = request.POST.getlist("data_pipe_size[]")

        for i in range(len(discharges_data)):
            MotorPumpData.objects.create(
                product=product,
                discharge=discharges_data[i],
                head=heads[i],
                recommend=(recommends[i] == '1'),
                motor_rating=MotorRating.objects.filter(id=motor_ratings_data[i]).first(),
                pipe_size=PipeSize.objects.filter(id=pipe_sizes_data[i]).first(),
                phase=phase  # Optional: set same as main product phase
            )

        messages.success(request, 'Product added successfully.')
        return redirect('products')

    return render(request, 'add_product.html', {
        'categories': categories,
        'discharge_units': discharge_units,
        'motor_ratings': motor_ratings,
        'phases': phases,
        'rpms': rpms,
        'pipe_sizes': pipe_sizes,
        'discharges': discharges,
        'hertzs': hertzs
    })




def edit_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.model_name = request.POST.get('model_name')
        product.account = request.POST.get('account')

        # 🔧 Convert IDs to model instances for ForeignKeys
        unit_id = request.POST.get('unit')
        motor_rating_id = request.POST.get('motor_rating')
        phase_id = request.POST.get('phase')
        rpm_id = request.POST.get('rpm')
        pipe_size_id = request.POST.get('pipe_size')
        hertz_id = request.POST.get('hertz')


        product.unit = DischargeUnit.objects.filter(id=unit_id).first()
        product.hertz = Hertz.objects.filter(id=hertz_id).first()  # ✅
        product.motor_rating = MotorRating.objects.filter(id=motor_rating_id).first()
        product.phase = Phase.objects.filter(id=phase_id).first()
        product.rpm = RPM.objects.filter(id=rpm_id).first()
        product.pipe_size = PipeSize.objects.filter(id=pipe_size_id).first()

        product.status = 'status' in request.POST

        # ✅ Handle ManyToMany fields
        category_ids = request.POST.getlist('categories')
        discharge_ids = request.POST.getlist('discharge')

        # ✅ Handle image uploads if present
        if request.FILES.get('thumb_image'):
            product.thumb_image = request.FILES['thumb_image']
        if request.FILES.get('preview_image'):
            product.preview_image = request.FILES['preview_image']

        # ✅ Save product and set ManyToMany fields
        product.save()
        product.categories.set(category_ids)
        product.discharge.set(discharge_ids)

        return redirect('products')

    context = {
        'product': product,
        'categories': Category.objects.all(),
        'selected_categories': list(product.categories.values_list('id', flat=True)),
        'discharges': Discharge.objects.all(),
        'selected_discharges': list(product.discharge.values_list('id', flat=True)),
        'motor_ratings': MotorRating.objects.all(),
        'phases': Phase.objects.all(),
        'rpms': RPM.objects.all(),
        'pipe_sizes': PipeSize.objects.all(),
        'units': DischargeUnit.objects.all(),
        'hertzs': Hertz.objects.all(),  # ✅
    }
    return render(request, 'edit_product.html', context)

def delete_product(request, id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=id)
        product.delete()
        messages.success(request, 'Product deleted successfully.')
    else:
        messages.error(request, 'Invalid request method.')

    return redirect('products')  # replace 'products' with your actual product list view name

def edit_fill_data(request, id):
    product = get_object_or_404(Product, id=id)
    discharges = Discharge.objects.all().order_by("discharge")
  
    hertzs = Hertz.objects.all()
    rpms = RPM.objects.all()
    units = DischargeUnit.objects.all()

    # ✅ Existing MotorPumpData
    existing_data = MotorPumpData.objects.filter(product=product)

    # ✅ Map discharge => MotorPumpData
    discharge_map = {int(mp.discharge): mp for mp in existing_data}

    if request.method == "POST":
        product.model_name = request.POST.get("model_name")
        product.account = request.POST.get("account")
        product.hertz_id = request.POST.get("hertz") or None
        product.rpm_id = request.POST.get("rpm") or None
        product.unit_id = request.POST.get("unit") or None
        product.status = 'status' in request.POST

        if request.FILES.get("thumb_image"):
            product.thumb_image = request.FILES["thumb_image"]
        product.save()

        # ✅ Remove old MotorPumpData before saving new
        existing_data.delete()

        discharges_data = request.POST.getlist("discharge[]")
        heads = request.POST.getlist("head[]")
        motor_ratings_data = request.POST.getlist("data_motor_rating[]")
        pipe_sizes_data = request.POST.getlist("data_pipe_size[]")

        for i in range(len(discharges_data)):
            MotorPumpData.objects.create(
                product=product,
                discharge=discharges_data[i],
                head=heads[i],
                recommend=(f"recommend_{i+1}" in request.POST),
                motor_rating_id=motor_ratings_data[i],
                pipe_size_id=pipe_sizes_data[i],
                phase=product.phase
            )

        return redirect("products")

    return render(request, "edit_fill_data.html", {
        "product": product,
        "discharges": discharges,
        "hertzs": hertzs,
        "rpms": rpms,
        "units": units,
        "discharge_map": discharge_map,  # ✅ Send this to template
    })

def view_product(request, id):
    product = get_object_or_404(Product, id=id)
    discharge_data = Discharge.objects.filter(product=product)

    context = {
        'product': product,
        'discharge_data': discharge_data,
        'discharges': product.unit.discharges.all() if product.unit else [],  # ✅ uses related_name
        'categories': product.categories.all(),
    }
    return render(request, 'view_product.html', context)