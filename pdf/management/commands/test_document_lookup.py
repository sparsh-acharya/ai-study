from django.core.management.base import BaseCommand
from pdf.models import Document, StudyPlan
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Test document lookup logic'

    def handle(self, *args, **options):
        # Get the latest document
        doc = Document.objects.last()
        if not doc:
            self.stdout.write(self.style.ERROR('No documents found'))
            return
            
        self.stdout.write(f'Latest document:')
        self.stdout.write(f'  ID: {doc.id}')
        self.stdout.write(f'  File name: {doc.file_name}')
        self.stdout.write(f'  File path: {doc.file}')
        
        # Simulate the lookup logic from analyze view
        file_url = f'/media/{doc.file}'
        file_name = file_url.split('/')[-1]
        self.stdout.write(f'\nSimulating lookup with file_name: {file_name}')
        
        # Try to find document by the actual file path first
        found_doc = Document.objects.filter(file=file_name).first()
        if found_doc:
            self.stdout.write(self.style.SUCCESS(f'Found document by file path: {found_doc}'))
        else:
            self.stdout.write(self.style.WARNING('Document not found by file path'))
            # Fallback: try to match by original filename
            found_doc = Document.objects.filter(file_name__icontains=file_name.split('_')[0]).first()
            if found_doc:
                self.stdout.write(self.style.SUCCESS(f'Found document by filename fallback: {found_doc}'))
            else:
                self.stdout.write(self.style.ERROR('Document not found by any method'))
        
        # Check study plans
        study_plans = StudyPlan.objects.all()
        self.stdout.write(f'\nStudy plans in database: {study_plans.count()}')
        for plan in study_plans:
            self.stdout.write(f'  - {plan.course_name} (User: {plan.user})')
