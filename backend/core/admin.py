from django.contrib import admin
from .models import Entry, Note, Document, Tag

admin.site.register(Entry)
admin.site.register(Note)
admin.site.register(Document)
admin.site.register(Tag)
