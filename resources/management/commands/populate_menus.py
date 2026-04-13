from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.urls import reverse

from cms.models import Menu, MenuItem
from resources.models import ResourceItem


class Command(BaseCommand):
    help = "Prepopulate Some basic important menu and menuitems."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Preparing menus and menu items...")
        )

        menus = (
            "primary_header",
            "footer",
        )
        resource_types = dict(ResourceItem._meta.get_field("resource_type").choices)
        print(resource_types)
        menus_created = 0
        for menu in menus:
            print(menu)
            print(type(menu))
            menu, created = Menu.objects.get_or_create(
                name=menu
            )
            if created:
                menus_created += 1

        menu_items_created = 0
        header_menu = Menu.objects.get(name='primary_header')
        print(header_menu)
        print(type(header_menu))
        if header_menu:
            header_menu_items = [
                "Resources",
            ]
            for menu_item in header_menu_items:
                menu_item, created = MenuItem.objects.get_or_create(
                    menu=header_menu,
                    title=menu_item,
                    url="#"
                )
                if created:
                    menu_items_created += 1

                resources_menu_items = MenuItem.objects.filter(
                    Q(title__exact='Resources') & Q(parent__exact=None)
                )
                print(resources_menu_items)
                for resource_menu_item in resources_menu_items:
                    resource_type_keys = resource_types.keys()
                    resource_type_values = resource_types.values()

                    for resource_type, resource_type_value in (resource_type_keys, resource_type_values):
                        url = reverse("resources:type_detail", kwargs={"resource_type": resource_type})
                        resource_sub_menu_items, created = MenuItem.objects.get_or_create(
                            menu=resource_menu_item.menu,
                            parent=menu_item,
                            url=url,
                            title=resource_type_value,
                        )
                        if created:
                            print(created)
