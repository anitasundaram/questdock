from django.db import models
from wagtail.models import Page
from wagtail.fields import StreamField, RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

class HomePage(Page):
    """Home page model"""
    
    # Hero section
    hero_title = models.CharField(max_length=200, blank=True)
    hero_subtitle = models.CharField(max_length=500, blank=True)
    hero_cta_text = models.CharField(max_length=100, default="Start Assessment")
    hero_cta_link = models.URLField(default="/assessment/start/")
    
    # Main content sections using StreamField for flexibility
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('feature_section', blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('features', blocks.ListBlock(blocks.StructBlock([
                ('icon', blocks.CharBlock(help_text='Font Awesome class name')),
                ('title', blocks.CharBlock()),
                ('description', blocks.TextBlock()),
            ]))),
        ])),
        ('testimonial', blocks.StructBlock([
            ('quote', blocks.TextBlock()),
            ('author', blocks.CharBlock()),
            ('role', blocks.CharBlock()),
        ])),
    ], use_json_field=True)
    
    # SEO and metadata
    meta_description = models.CharField(max_length=255, blank=True)
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel('hero_cta_text'),
            FieldPanel('hero_cta_link'),
        ], heading="Hero Section"),
        FieldPanel('body'),
    ]
    
    promote_panels = Page.promote_panels + [
        FieldPanel('meta_description'),
    ]

    class Meta:
        verbose_name = "Home Page"