# Generated starter migration for LAFRE Citizens
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [

        migrations.CreateModel(
            name='CitizenProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=40)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='citizen_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Matter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pathway_key', models.CharField(max_length=80)),
                ('pathway_title', models.CharField(max_length=120)),
                ('title', models.CharField(max_length=180)),
                ('status', models.CharField(choices=[('collecting_info', 'Collecting information'), ('document_generated', 'Document generated'), ('needs_review', 'Needs review'), ('sent_to_lawyer', 'Sent to lawyer'), ('reviewed', 'Reviewed'), ('ready_to_sign', 'Ready to sign'), ('signed', 'Signed'), ('archived', 'Archived')], default='collecting_info', max_length=32)),
                ('risk_level', models.CharField(default='Medium', max_length=40)),
                ('summary', models.TextField(blank=True)),
                ('next_steps', models.JSONField(blank=True, default=list)),
                ('flags', models.JSONField(blank=True, default=list)),
                ('answers', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citizen_pathway_matters', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-updated_at']},
        ),
        migrations.CreateModel(
            name='GeneratedDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(max_length=80)),
                ('version', models.PositiveIntegerField(default=1)),
                ('content', models.TextField()),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='citizen_documents/')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('matter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='citizens.matter')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='MatterEvidence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evidence_type', models.CharField(choices=[('id', 'ID document'), ('proof_of_payment', 'Proof of payment'), ('receipt', 'Receipt'), ('screenshot', 'Screenshot'), ('signed_document', 'Signed document'), ('collateral_photo', 'Collateral photo'), ('other', 'Other')], default='other', max_length=40)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('file', models.FileField(upload_to='citizen_evidence/')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('matter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evidence', to='citizens.matter')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='LawyerReviewRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_type', models.CharField(choices=[('document_check', 'Document check'), ('certification', 'Certification / validation'), ('consultation', 'Consultation request')], default='document_check', max_length=40)),
                ('fixed_fee', models.DecimalField(decimal_places=2, default=3.0, max_digits=10)),
                ('payment_status', models.CharField(default='pending', max_length=30)),
                ('review_status', models.CharField(choices=[('draft', 'Draft'), ('payment_pending', 'Payment pending'), ('submitted', 'Submitted'), ('assigned', 'Assigned'), ('reviewed', 'Reviewed'), ('cancelled', 'Cancelled')], default='payment_pending', max_length=30)),
                ('mock_lawyer_name', models.CharField(default='LAFRE Review Desk', max_length=120)),
                ('lawyer_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('matter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_requests', to='citizens.matter')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SimulatedPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(default='EcoCash Simulation', max_length=40)),
                ('phone_number', models.CharField(max_length=40)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reference', models.CharField(max_length=80, unique=True)),
                ('status', models.CharField(default='success', max_length=30)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('review_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='citizens.lawyerreviewrequest')),
            ],
        ),
    ]
