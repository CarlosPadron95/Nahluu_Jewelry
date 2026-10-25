"""
Panel de administración del catálogo.

Es la herramienta con la que Andrea dará de alta las joyas, subirá
las fotos y controlará el stock. Todo en español y lo más claro posible.
"""

from django.contrib import admin, messages
from django.db.models import Count
from django.utils import timezone
from django.utils.html import format_html

from .forms import ProductAdminForm, ProductImageInlineFormSet
from .models import Category, Collection, Product, ProductImage


def photo_thumbnail(photo, size=64):
    """Miniatura de una foto para las listas del panel."""
    if not photo:
        return "—"
    return format_html(
        '<img src="{}" alt="" width="{}" height="{}" '
        'style="object-fit: cover; border-radius: 4px;">',
        photo.url,
        size,
        size,
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name_es", "name_en", "product_count", "position"]
    list_editable = ["position"]
    prepopulated_fields = {"slug": ["name_es"]}
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        # Contamos los productos de cada categoría en la misma consulta
        return super().get_queryset(request).annotate(product_count=Count("products"))

    @admin.display(description="productos", ordering="product_count")
    def product_count(self, obj):
        return obj.product_count


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["thumbnail", "name_es", "name_en", "product_count", "position", "is_active"]
    list_display_links = ["thumbnail", "name_es"]
    list_editable = ["position", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name_es", "name_en"]
    prepopulated_fields = {"slug": ["name_es"]}
    readonly_fields = ["current_photo", "created_at", "updated_at"]
    fieldsets = [
        ("Español", {"fields": ["name_es", "slug", "description_es"]}),
        ("Inglés", {"fields": ["name_en", "description_en"]}),
        ("Foto", {"fields": ["current_photo", "image"]}),
        ("Escaparate", {"fields": ["position", "is_active"]}),
        ("Fechas", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(product_count=Count("products"))

    @admin.display(description="foto")
    def thumbnail(self, obj):
        return photo_thumbnail(obj.image)

    @admin.display(description="foto actual")
    def current_photo(self, obj):
        return photo_thumbnail(obj.image, size=200)

    @admin.display(description="productos", ordering="product_count")
    def product_count(self, obj):
        return obj.product_count


class ProductImageInline(admin.TabularInline):
    """Las fotos se suben desde la propia ficha del producto."""

    model = ProductImage
    formset = ProductImageInlineFormSet
    extra = 1
    fields = ["preview", "image", "alt_es", "alt_en", "position"]
    readonly_fields = ["preview"]

    @admin.display(description="vista previa")
    def preview(self, obj):
        return photo_thumbnail(obj.image, size=96)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    inlines = [ProductImageInline]
    save_on_top = True  # botones de guardar también arriba (la ficha es larga)

    # --- Lista de productos ---
    list_display = [
        "thumbnail",
        "name_es",
        "category",
        "price_in_euros",
        "stock",
        "shop_labels",
        "is_active",
    ]
    list_display_links = ["thumbnail", "name_es"]
    # El stock se puede cambiar directamente desde la lista
    list_editable = ["stock"]
    list_filter = ["is_active", "category", "collection", "is_new", "is_featured"]
    search_fields = ["name_es", "name_en", "slug"]
    list_select_related = ["category", "collection"]
    list_per_page = 50
    actions = ["publish", "unpublish"]

    # --- Ficha del producto ---
    prepopulated_fields = {"slug": ["name_es"]}
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        ("Español", {"fields": ["name_es", "slug", "description_es", "details_es"]}),
        (
            "Inglés",
            {
                "fields": ["name_en", "description_en", "details_en"],
                "description": "Obligatorio para publicar: la tienda vende a todo el mundo.",
            },
        ),
        ("Organización", {"fields": ["category", "collection", "position"]}),
        ("Precio y stock", {"fields": ["price", "stock", "weight_grams"]}),
        ("Escaparate", {"fields": ["is_active", "is_new", "is_featured"]}),
        ("Fechas", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    def get_queryset(self, request):
        # Traemos las fotos de golpe para las miniaturas (una consulta, no una por producto)
        return super().get_queryset(request).prefetch_related("images")

    @admin.display(description="foto")
    def thumbnail(self, obj):
        first_photo = next(iter(obj.images.all()), None)
        return photo_thumbnail(first_photo.image if first_photo else None)

    @admin.display(description="precio", ordering="price_cents")
    def price_in_euros(self, obj):
        return obj.price_display

    @admin.display(description="etiquetas")
    def shop_labels(self, obj):
        return " · ".join(obj.labels) or "—"

    @admin.action(description="Publicar los productos seleccionados")
    def publish(self, request, queryset):
        """Publica solo los productos completos y avisa de lo que falta en los demás."""
        published = 0
        for product in queryset:
            problems = product.publishing_problems()
            if problems:
                self.message_user(
                    request,
                    f"«{product}» no se ha publicado: {', '.join(problems)}.",
                    messages.WARNING,
                )
                continue
            product.is_active = True
            product.save(update_fields=["is_active", "updated_at"])
            published += 1

        if published:
            self.message_user(request, f"Productos publicados: {published}.", messages.SUCCESS)

    @admin.action(description="Ocultar los productos seleccionados")
    def unpublish(self, request, queryset):
        hidden = queryset.update(is_active=False, updated_at=timezone.now())
        self.message_user(request, f"Productos ocultados: {hidden}.", messages.SUCCESS)
