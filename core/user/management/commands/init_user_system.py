# core/user/management/commands/init_user_system.py

"""
Management command para inicializar el sistema de usuarios.
Crea roles, permisos y datos de prueba si es necesario.

Uso:
    python manage.py init_user_system
    python manage.py init_user_system --create-demo-users
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.user.models import UserAccount, Role, Permission
from core.user.api.services_advanced import RoleService


class Command(BaseCommand):
    help = 'Inicializa el sistema de usuarios con roles y permisos por defecto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-demo-users',
            action='store_true',
            help='Crea usuarios de demostración',
        )
        
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Resetea roles y permisos existentes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando configuración del sistema de usuarios...'))
        
        with transaction.atomic():
            # 1. Inicializar roles y permisos
            if options['reset']:
                self.stdout.write(self.style.WARNING('⚠️  Limpiando roles y permisos existentes...'))
                Permission.objects.all().delete()
                Role.objects.filter(is_system_role=False).delete()
            
            self.stdout.write('📋 Creando permisos...')
            self.create_permissions()
            
            self.stdout.write('👥 Creando roles...')
            self.create_roles()
            
            # 2. Crear usuarios de demo si se solicita
            if options['create_demo_users']:
                self.stdout.write('👤 Creando usuarios de demostración...')
                self.create_demo_users()
            
            self.stdout.write(self.style.SUCCESS('✅ Sistema inicializado correctamente!'))
            self.print_summary()

    def create_permissions(self):
        """Crea todos los permisos del sistema."""
        permissions_data = [
            # Permisos de Productos
            ('product.view', 'Ver Productos', 'product', 'Puede ver todos los productos'),
            ('product.create', 'Crear Productos', 'product', 'Puede crear nuevos productos'),
            ('product.edit', 'Editar Productos', 'product', 'Puede editar productos existentes'),
            ('product.delete', 'Eliminar Productos', 'product', 'Puede eliminar productos'),
            ('product.approve', 'Aprobar Productos', 'product', 'Puede aprobar productos pendientes'),
            
            # Permisos de Usuarios
            ('user.view', 'Ver Usuarios', 'user', 'Puede ver listado de usuarios'),
            ('user.edit', 'Editar Usuarios', 'user', 'Puede editar información de usuarios'),
            ('user.delete', 'Eliminar Usuarios', 'user', 'Puede eliminar usuarios'),
            ('user.manage_roles', 'Gestionar Roles', 'user', 'Puede asignar/quitar roles'),
            
            # Permisos de Órdenes
            ('order.view', 'Ver Órdenes', 'order', 'Puede ver todas las órdenes'),
            ('order.create', 'Crear Órdenes', 'order', 'Puede crear órdenes'),
            ('order.edit', 'Editar Órdenes', 'order', 'Puede modificar órdenes'),
            ('order.cancel', 'Cancelar Órdenes', 'order', 'Puede cancelar órdenes'),
            ('order.manage', 'Gestionar Órdenes', 'order', 'Control completo de órdenes'),
            
            # Permisos de Reviews
            ('review.view', 'Ver Reviews', 'review', 'Puede ver todas las reviews'),
            ('review.moderate', 'Moderar Reviews', 'review', 'Puede aprobar/rechazar reviews'),
            ('review.delete', 'Eliminar Reviews', 'review', 'Puede eliminar reviews'),
            
            # Permisos de Campañas
            ('campaign.view', 'Ver Campañas', 'campaign', 'Puede ver campañas'),
            ('campaign.create', 'Crear Campañas', 'campaign', 'Puede crear campañas'),
            ('campaign.edit', 'Editar Campañas', 'campaign', 'Puede editar campañas'),
            ('campaign.delete', 'Eliminar Campañas', 'campaign', 'Puede eliminar campañas'),
            
            # Permisos de Analytics
            ('analytics.view', 'Ver Analytics', 'analytics', 'Acceso a estadísticas'),
            ('analytics.export', 'Exportar Datos', 'analytics', 'Puede exportar datos'),
            
            # Permisos de Configuración
            ('settings.view', 'Ver Configuración', 'settings', 'Puede ver configuración'),
            ('settings.edit', 'Editar Configuración', 'settings', 'Puede modificar configuración'),
        ]
        
        created = 0
        for code, name, module, description in permissions_data:
            perm, created_now = Permission.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'module': module,
                    'description': description
                }
            )
            if created_now:
                created += 1
                self.stdout.write(f'  ✓ {code}')
        
        self.stdout.write(self.style.SUCCESS(f'  → {created} permisos creados'))

    def create_roles(self):
        """Crea los roles del sistema."""
        # Rol: Administrador (todos los permisos)
        admin_role, created = Role.objects.get_or_create(
            name='Admin',
            defaults={
                'description': 'Administrador con acceso completo al sistema',
                'is_system_role': True
            }
        )
        admin_role.permissions.set(Permission.objects.all())
        if created:
            self.stdout.write('  ✓ Rol Admin creado')
        
        # Rol: Moderador (gestión de contenido)
        moderator_role, created = Role.objects.get_or_create(
            name='Moderator',
            defaults={
                'description': 'Moderador de contenido y reviews',
                'is_system_role': True
            }
        )
        moderator_perms = Permission.objects.filter(
            code__in=[
                'product.view', 'product.edit', 'product.approve',
                'review.view', 'review.moderate', 'review.delete',
                'order.view', 'user.view'
            ]
        )
        moderator_role.permissions.set(moderator_perms)
        if created:
            self.stdout.write('  ✓ Rol Moderator creado')
        
        # Rol: Designer (gestión de productos)
        designer_role, created = Role.objects.get_or_create(
            name='Designer',
            defaults={
                'description': 'Diseñador con permisos para crear y editar productos',
                'is_system_role': True
            }
        )
        designer_perms = Permission.objects.filter(
            code__in=[
                'product.view', 'product.create', 'product.edit',
                'campaign.view', 'campaign.create', 'campaign.edit'
            ]
        )
        designer_role.permissions.set(designer_perms)
        if created:
            self.stdout.write('  ✓ Rol Designer creado')
        
        # Rol: Customer Support (atención al cliente)
        support_role, created = Role.objects.get_or_create(
            name='Support',
            defaults={
                'description': 'Soporte al cliente',
                'is_system_role': True
            }
        )
        support_perms = Permission.objects.filter(
            code__in=[
                'order.view', 'order.edit', 'order.cancel',
                'user.view', 'product.view', 'review.view'
            ]
        )
        support_role.permissions.set(support_perms)
        if created:
            self.stdout.write('  ✓ Rol Support creado')
        
        # Rol: Customer (usuario básico)
        customer_role, created = Role.objects.get_or_create(
            name='Customer',
            defaults={
                'description': 'Cliente con permisos básicos',
                'is_system_role': True
            }
        )
        customer_perms = Permission.objects.filter(
            code__in=[
                'product.view', 'order.view', 'order.create', 'review.view'
            ]
        )
        customer_role.permissions.set(customer_perms)
        if created:
            self.stdout.write('  ✓ Rol Customer creado')
        
        # Rol: Analyst (acceso a analytics)
        analyst_role, created = Role.objects.get_or_create(
            name='Analyst',
            defaults={
                'description': 'Analista con acceso a estadísticas',
                'is_system_role': True
            }
        )
        analyst_perms = Permission.objects.filter(
            code__in=[
                'analytics.view', 'analytics.export',
                'product.view', 'order.view', 'user.view'
            ]
        )
        analyst_role.permissions.set(analyst_perms)
        if created:
            self.stdout.write('  ✓ Rol Analyst creado')
        
        self.stdout.write(self.style.SUCCESS('  → Roles configurados'))

    def create_demo_users(self):
        """Crea usuarios de demostración para testing."""
        demo_users = [
            {
                'email': 'admin@demo.com',
                'password': 'Demo1234!',
                'first_name': 'Admin',
                'last_name': 'Demo',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
                'roles': ['Admin']
            },
            {
                'email': 'moderator@demo.com',
                'password': 'Demo1234!',
                'first_name': 'Moderator',
                'last_name': 'Demo',
                'is_staff': True,
                'is_verified': True,
                'roles': ['Moderator']
            },
            {
                'email': 'designer@demo.com',
                'password': 'Demo1234!',
                'first_name': 'Designer',
                'last_name': 'Demo',
                'is_verified': True,
                'roles': ['Designer']
            },
            {
                'email': 'support@demo.com',
                'password': 'Demo1234!',
                'first_name': 'Support',
                'last_name': 'Demo',
                'is_verified': True,
                'roles': ['Support']
            },
            {
                'email': 'customer@demo.com',
                'password': 'Demo1234!',
                'first_name': 'Customer',
                'last_name': 'Demo',
                'is_verified': True,
                'roles': ['Customer']
            },
        ]
        
        created = 0
        for user_data in demo_users:
            roles = user_data.pop('roles', [])
            
            if not UserAccount.objects.filter(email=user_data['email']).exists():
                user = UserAccount.objects.create_user(**user_data)
                
                # Asignar roles
                for role_name in roles:
                    try:
                        role = Role.objects.get(name=role_name)
                        user.roles.add(role)
                    except Role.DoesNotExist:
                        pass
                
                created += 1
                self.stdout.write(f'  ✓ {user.email} (password: Demo1234!)')
        
        self.stdout.write(self.style.SUCCESS(f'  → {created} usuarios demo creados'))

    def print_summary(self):
        """Imprime un resumen de la configuración."""
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('RESUMEN DEL SISTEMA'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        total_users = UserAccount.objects.count()
        total_roles = Role.objects.count()
        total_permissions = Permission.objects.count()
        
        self.stdout.write(f'📊 Total de usuarios: {total_users}')
        self.stdout.write(f'👥 Total de roles: {total_roles}')
        self.stdout.write(f'🔑 Total de permisos: {total_permissions}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('ROLES DISPONIBLES:'))
        for role in Role.objects.all():
            perm_count = role.permissions.count()
            user_count = role.users.count()
            self.stdout.write(
                f'  • {role.name} ({perm_count} permisos, {user_count} usuarios)'
            )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Sistema listo para usar! 🚀'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write('Accede al admin en: http://localhost:8000/admin/')
        self.stdout.write('')
