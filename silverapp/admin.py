from django.contrib import admin
from .models import *

# Register your models here.
class sadmin(admin.ModelAdmin):
    list_display=['username','password']

admin.site.register(login_tbl,sadmin)
# class addsubuserAdmin(admin.ModelAdmin):
#     list_display=['image','new_password','email','login_id','foldername','licence_domain','embed_licence','licence_logo','tools_logo','login_screenlogo','firstname','lastname','access_code','address','zipcode','mobile','fax','database_host','db_username',' db_name','db_password',' is_blocked']
admin.site.register(add_subuser)