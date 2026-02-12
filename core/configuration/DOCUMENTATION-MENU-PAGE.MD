# 📚 DOCUMENTACIÓN COMPLETA - SISTEMA DE MENÚS Y PÁGINAS

## 📖 Índice

1. [Resumen General](#resumen-general)
2. [Instalación](#instalación)
3. [Modelo Menu](#modelo-menu)
4. [Modelo Page](#modelo-page)
5. [API Endpoints](#api-endpoints)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Admin](#admin)
8. [Frontend Integration](#frontend-integration)

---

## 🎯 Resumen General

Sistema completo de **Menús Jerárquicos** y **Páginas Estáticas** para Django, inspirado en WordPress pero mejorado.

### Características Principales

#### 🔗 Sistema de Menús
- ✅ Menús jerárquicos ilimitados (MPTT)
- ✅ Múltiples tipos (Header, Footer, Mobile, Sidebar)
- ✅ Enlaces flexibles (URL, Categoría, Página, Externo, Mega Menú)
- ✅ Drag & Drop en admin
- ✅ Iconos y clases CSS personalizadas
- ✅ Mega menús con columnas
- ✅ API completa con árbol jerárquico

#### 📄 Sistema de Páginas
- ✅ Páginas estáticas (Privacidad, Términos, Ayuda, etc)
- ✅ Editor WYSIWYG (TinyMCE)
- ✅ Múltiples plantillas
- ✅ SEO completo (meta tags)
- ✅ Programación de publicación
- ✅ Páginas protegidas por autenticación
- ✅ Tiempo de lectura estimado

---

## 🚀 Instalación

### Paso 1: Verificar Dependencias

```bash
# Asegúrate de tener instalado:
pip install django-mptt
pip install django-tinymce
pip install easy-thumbnails
```

### Paso 2: Copiar Archivos

```cmd
REM Copiar modelos actualizados
copy configuration_models.py core\configuration\models.py

REM Copiar admin actualizado
copy configuration_admin.py core\configuration\admin.py

REM Copiar endpoints actualizados
copy configuration_endpoints.py core\configuration\api\endpoints.py

REM Copiar schemas actualizados
copy configuration_schemas.py core\configuration\api\schemas.py
```

### Paso 3: Configurar TinyMCE

En `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'mptt',
    'tinymce',
    'easy_thumbnails',
    'core.configuration',
    # ...
]

# Configuración de TinyMCE
TINYMCE_DEFAULT_CONFIG = {
    'height': 500,
    'width': '100%',
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea',
    'theme': 'silver',
    'plugins': '''
        textcolor save link image media preview codesample contextmenu
        table code lists fullscreen  insertdatetime  nonbreaking
        contextmenu directionality searchreplace wordcount visualblocks
        visualchars code fullscreen autolink lists charmap print hr
        anchor pagebreak
    ''',
    'toolbar1': '''
        fullscreen preview bold italic underline | fontselect,
        fontsizeselect  | forecolor backcolor | alignleft alignright |
        aligncenter alignjustify | indent outdent | bullist numlist table |
        | link image media | codesample |
    ''',
    'toolbar2': '''
        visualblocks visualchars |
        charmap hr pagebreak nonbreaking anchor |  code |
    ''',
    'contextmenu': 'formats | link image',
    'menubar': True,
    'statusbar': True,
}
```

### Paso 4: Migraciones

```bash
python manage.py makemigrations configuration
python manage.py migrate
```

### Paso 5: Registrar en API

En tu `app/api.py`:

```python
from core.configuration.api.endpoints import router as config_router

api.add_router("/config/", config_router, tags=["Configuración"])
```

---

## 🔗 Modelo Menu

### Estructura del Modelo

```python
class Menu(MPTTModel):
    # Básico
    name = CharField  # Texto del menú
    slug = SlugField  # URL amigable
    parent = TreeForeignKey  # Padre (jerarquía)
    
    # Tipo y ubicación
    menu_type = CharField  # header, footer, mobile, sidebar, custom
    link_type = CharField  # url, category, page, external, megamenu
    
    # Enlaces
    url = CharField  # URL personalizada
    category = ForeignKey(Category)  # Enlace a categoría
    page = ForeignKey(Page)  # Enlace a página
    
    # Visual
    icon = CharField  # Clase de icono
    image = ImageField  # Imagen opcional
    description = TextField  # Descripción
    css_classes = CharField  # Clases CSS
    
    # Configuración
    order = IntegerField  # Orden
    is_active = BooleanField  # Activo/Inactivo
    is_featured = BooleanField  # Destacado
    open_in_new_tab = BooleanField  # target="_blank"
    mega_menu_columns = IntegerField  # Columnas si es mega menú
```

### Tipos de Menú Disponibles

| Tipo | Descripción | Uso |
|------|-------------|-----|
| `header` | Menú Principal | Navegación superior |
| `footer` | Menú Footer | Enlaces del pie de página |
| `mobile` | Menú Móvil | Hamburger menu |
| `sidebar` | Menú Lateral | Categorías laterales |
| `custom` | Personalizado | Cualquier otro uso |

### Tipos de Enlace

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `url` | URL Personalizada | `/shop`, `/about` |
| `category` | Enlace a Categoría | Selecciona de lista |
| `page` | Enlace a Página | Selecciona de lista |
| `external` | Enlace Externo | `https://google.com` |
| `megamenu` | Mega Menú | Solo contenedor |

### Métodos Principales

```python
menu = Menu.objects.get(id=1)

# Obtener URL final
url = menu.get_url()  # Retorna URL según tipo

# Verificar hijos
has_children = menu.has_children()  # True/False

# Obtener hijos activos
children = menu.get_active_children()

# Obtener clases CSS como lista
classes = menu.get_css_classes_list()

# URL de imagen
image_url = menu.image_url  # Property
```

### Validaciones Automáticas

✅ Valida que URL esté presente si `link_type='url'`  
✅ Valida que categoría esté seleccionada si `link_type='category'`  
✅ Valida que página esté seleccionada si `link_type='page'`  
✅ Auto-genera slug único del nombre  

---

## 📄 Modelo Page

### Estructura del Modelo

```python
class Page(models.Model):
    # Básico
    title = CharField  # Título
    slug = SlugField  # URL amigable
    
    # Tipo y plantilla
    page_type = CharField  # legal, about, help, policy, custom
    template = CharField  # default, full_width, sidebar, landing, contact
    
    # Contenido
    content = HTMLField  # Contenido HTML (TinyMCE)
    excerpt = TextField  # Resumen corto
    featured_image = ImageField  # Imagen destacada
    
    # SEO
    meta_title = CharField  # Título SEO (70 chars)
    meta_description = CharField  # Descripción SEO (160 chars)
    meta_keywords = CharField  # Keywords
    
    # Configuración
    is_published = BooleanField  # Publicado
    show_in_menu = BooleanField  # Mostrar en menús
    require_auth = BooleanField  # Requiere login
    order = IntegerField  # Orden
    published_at = DateTimeField  # Fecha de publicación
```

### Tipos de Página

| Tipo | Descripción | Ejemplos |
|------|-------------|----------|
| `legal` | Legal | Privacidad, Términos |
| `about` | Institucional | Sobre Nosotros, Equipo |
| `help` | Ayuda/Soporte | FAQ, Guías |
| `policy` | Políticas | Devoluciones, Envíos |
| `custom` | Personalizada | Cualquier otra |

### Plantillas Disponibles

| Plantilla | Descripción |
|-----------|-------------|
| `default` | Plantilla estándar |
| `full_width` | Ancho completo sin sidebar |
| `sidebar` | Con barra lateral |
| `landing` | Landing page especial |
| `contact` | Página de contacto |

### Métodos Principales

```python
page = Page.objects.get(id=1)

# Verificar si está publicada
is_published = page.is_currently_published()

# URL de la página
url = page.get_absolute_url()  # /page/slug

# Tiempo de lectura
reading_time = page.get_reading_time()  # En minutos

# URL de imagen
image_url = page.featured_image_url  # Property
```

### Auto-generación de Campos

✅ Auto-genera `slug` del título  
✅ Auto-genera `meta_title` del título (si vacío)  
✅ Auto-genera `meta_description` del excerpt (si vacío)  
✅ Auto-establece `published_at` al publicar por primera vez  

---

## 🌐 API Endpoints

### Endpoints de Menu

#### 1. Listar Menús

```http
GET /api/config/menus/list

Query Parameters:
- menu_type: header, footer, mobile, sidebar, custom
- is_active: true/false
- search: Buscar texto
```

**Ejemplo:**
```bash
GET /api/config/menus/list?menu_type=header&is_active=true
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "name": "Home",
    "slug": "home",
    "menu_type": "header",
    "url": "/",
    "icon": "fa-home",
    "order": 0,
    "level": 0,
    "is_active": true
  }
]
```

---

#### 2. Obtener Árbol de Menú

```http
GET /api/config/menus/tree/{menu_type}
```

**Ejemplo:**
```bash
GET /api/config/menus/tree/header
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "name": "Shop",
    "slug": "shop",
    "url": "/shop",
    "icon": "fa-shopping-bag",
    "is_featured": false,
    "level": 0,
    "children": [
      {
        "id": 2,
        "name": "Categorías",
        "slug": "categorias",
        "url": "/categorias",
        "icon": null,
        "is_featured": false,
        "level": 1,
        "children": []
      }
    ]
  }
]
```

---

#### 3. Obtener Menú por ID/Slug

```http
GET /api/config/menus/{menu_id}
GET /api/config/menus/slug/{slug}
```

**Ejemplo:**
```bash
GET /api/config/menus/1
GET /api/config/menus/slug/shop-now
```

---

### Endpoints de Page

#### 1. Listar Páginas

```http
GET /api/config/pages/list

Query Parameters:
- page_type: legal, about, help, policy, custom
- is_published: true/false
- search: Buscar texto
```

**Ejemplo:**
```bash
GET /api/config/pages/list?page_type=legal
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "title": "Política de Privacidad",
    "slug": "politica-de-privacidad",
    "page_type": "legal",
    "page_type_display": "Legal",
    "excerpt": "Lee nuestra política de privacidad...",
    "featured_image_url": null,
    "is_published": true,
    "published_at": "2024-01-15T10:00:00Z",
    "reading_time": 5
  }
]
```

---

#### 2. Obtener Página por ID/Slug

```http
GET /api/config/pages/{page_id}
GET /api/config/pages/slug/{slug}
```

**Ejemplo:**
```bash
GET /api/config/pages/slug/politica-de-privacidad
```

**Respuesta:**
```json
{
  "id": 1,
  "title": "Política de Privacidad",
  "slug": "politica-de-privacidad",
  "page_type": "legal",
  "template": "default",
  "content": "<h1>Política de Privacidad</h1><p>...</p>",
  "excerpt": "Lee nuestra política...",
  "meta_title": "Política de Privacidad - Mi Tienda",
  "meta_description": "Lee nuestra política de privacidad...",
  "is_published": true,
  "reading_time": 5,
  "absolute_url": "/page/politica-de-privacidad"
}
```

---

#### 3. Páginas para Footer

```http
GET /api/config/pages/menu/footer
```

Retorna solo páginas marcadas como "mostrar en menú".

**Uso:** Links de Privacidad, Términos en el footer.

---

#### 4. Configuración Completa del Sitio

```http
GET /api/config/site
```

Retorna todo en una sola llamada:
- Menús de todos los tipos
- Páginas para footer
- Estadísticas

**Respuesta:**
```json
{
  "menus": {
    "header": [...],
    "footer": [...],
    "mobile": [...]
  },
  "footer_pages": [
    {
      "id": 1,
      "title": "Privacidad",
      "slug": "privacidad",
      "page_type": "legal"
    }
  ],
  "stats": {
    "total_menus": 10,
    "total_pages": 5
  }
}
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Menú de Navegación Principal

```javascript
// React/Next.js Component

async function loadMainMenu() {
  const response = await fetch('/api/config/menus/tree/header');
  const menus = await response.json();
  
  return menus;
}

function NavigationMenu() {
  const [menus, setMenus] = useState([]);
  
  useEffect(() => {
    loadMainMenu().then(setMenus);
  }, []);
  
  const renderMenu = (items) => (
    <ul>
      {items.map(item => (
        <li key={item.id}>
          <a href={item.url}>
            {item.icon && <i className={item.icon} />}
            {item.name}
          </a>
          {item.children.length > 0 && (
            <ul className="submenu">
              {renderMenu(item.children)}
            </ul>
          )}
        </li>
      ))}
    </ul>
  );
  
  return <nav>{renderMenu(menus)}</nav>;
}
```

---

### Ejemplo 2: Footer con Links Legales

```javascript
async function loadFooterPages() {
  const response = await fetch('/api/config/pages/menu/footer');
  const pages = await response.json();
  
  return pages;
}

function Footer() {
  const [pages, setPages] = useState([]);
  
  useEffect(() => {
    loadFooterPages().then(setPages);
  }, []);
  
  return (
    <footer>
      <div className="legal-links">
        {pages.map(page => (
          <a key={page.id} href={`/page/${page.slug}`}>
            {page.title}
          </a>
        ))}
      </div>
    </footer>
  );
}
```

---

### Ejemplo 3: Renderizar Página

```javascript
async function loadPage(slug) {
  const response = await fetch(`/api/config/pages/slug/${slug}`);
  const page = await response.json();
  
  return page;
}

function PageComponent({ slug }) {
  const [page, setPage] = useState(null);
  
  useEffect(() => {
    loadPage(slug).then(setPage);
  }, [slug]);
  
  if (!page) return <div>Cargando...</div>;
  
  return (
    <article>
      <h1>{page.title}</h1>
      
      {page.featured_image_url && (
        <img src={page.featured_image_url} alt={page.title} />
      )}
      
      <div 
        className="content"
        dangerouslySetInnerHTML={{ __html: page.content }}
      />
      
      <footer>
        <small>Tiempo de lectura: {page.reading_time} min</small>
      </footer>
    </article>
  );
}
```

---

### Ejemplo 4: SEO Meta Tags

```javascript
async function loadPageSEO(slug) {
  const response = await fetch(`/api/config/pages/seo/${slug}`);
  const seo = await response.json();
  
  return seo;
}

function PageHead({ slug }) {
  const [seo, setSeo] = useState(null);
  
  useEffect(() => {
    loadPageSEO(slug).then(setSeo);
  }, [slug]);
  
  if (!seo) return null;
  
  return (
    <Head>
      <title>{seo.meta_title}</title>
      <meta name="description" content={seo.meta_description} />
      {seo.meta_keywords && (
        <meta name="keywords" content={seo.meta_keywords} />
      )}
      <link rel="canonical" href={`https://ejemplo.com${seo.absolute_url}`} />
    </Head>
  );
}
```

---

## 🎨 Admin

### Características del Admin de Menu

1. **Drag & Drop** - Reorganizar arrastrando
2. **Preview de URL** - Ver URL final antes de guardar
3. **Badges de Tipo** - Colores por tipo de menú
4. **Validaciones** - No permitir configuraciones inválidas
5. **Duplicar** - Acción para duplicar menús
6. **Activar/Desactivar** - Acciones masivas

### Características del Admin de Page

1. **Editor WYSIWYG** - TinyMCE completo
2. **Preview SEO** - Ver cómo se verá en Google
3. **Tiempo de Lectura** - Cálculo automático
4. **Programar Publicación** - Fechas futuras
5. **Preview de Imagen** - Vista previa grande
6. **Duplicar** - Acción para duplicar páginas

---

## ✅ Checklist de Implementación

- [ ] Dependencias instaladas (mppt, tinymce)
- [ ] Archivos copiados
- [ ] Migraciones ejecutadas
- [ ] Router registrado en API
- [ ] TinyMCE configurado
- [ ] Crear menús de prueba
- [ ] Crear páginas de prueba
- [ ] Probar endpoints
- [ ] Integrar en frontend

---

## 🎓 Mejores Prácticas

### Para Menús

1. ✅ Usa `menu_type` apropiado para cada ubicación
2. ✅ No crear más de 3 niveles de profundidad
3. ✅ Usa iconos consistentes (FontAwesome, Lucide, etc)
4. ✅ Mantén nombres cortos (máx 20 caracteres)
5. ✅ Usa `is_featured` para destacar items importantes

### Para Páginas

1. ✅ Escribe meta descriptions únicas (máx 160 chars)
2. ✅ Usa headings jerárquicos (H1, H2, H3)
3. ✅ Optimiza imágenes antes de subir
4. ✅ Marca como "mostrar en menú" solo las esenciales
5. ✅ Usa extractos atractivos

---

## 📊 Resumen de Archivos

| Archivo | Descripción | Líneas |
|---------|-------------|--------|
| `models.py` | Modelos Menu y Page | ~800 |
| `admin.py` | Admin completo | ~500 |
| `endpoints.py` | 20+ endpoints API | ~500 |
| `schemas.py` | Schemas Ninja | ~200 |

**Total:** ~2,000 líneas de código profesional

---

**¿Necesitas algo más específico?**
- Agregar más tipos de página
- Crear templates personalizados
- Integración con redes sociales
- Sistema de comentarios

¡Ya tienes un CMS completo integrado! 🚀