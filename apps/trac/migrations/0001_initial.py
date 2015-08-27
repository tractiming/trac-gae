# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Coach'
        db.create_table(u'trac_coach', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('payment', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True)),
        ))
        db.send_create_signal(u'trac', ['Coach'])

        # Adding model 'Team'
        db.create_table(u'trac_team', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('coach', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trac.Coach'])),
            ('tfrrs_code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
        ))
        db.send_create_signal(u'trac', ['Team'])

        # Adding model 'Athlete'
        db.create_table(u'trac_athlete', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trac.Team'], null=True, blank=True)),
            ('birth_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('tfrrs_id', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('year', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
        ))
        db.send_create_signal(u'trac', ['Athlete'])

        # Adding model 'Tag'
        db.create_table(u'trac_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('id_str', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('athlete', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['trac.Athlete'], unique=True)),
        ))
        db.send_create_signal(u'trac', ['Tag'])

        # Adding model 'Reader'
        db.create_table(u'trac_reader', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('id_str', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('coach', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trac.Coach'])),
        ))
        db.send_create_signal(u'trac', ['Reader'])

        # Adding model 'Split'
        db.create_table(u'trac_split', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trac.Tag'])),
            ('athlete', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trac.Athlete'])),
            ('reader', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trac.Reader'])),
            ('time', self.gf('django.db.models.fields.BigIntegerField')()),
        ))
        db.send_create_signal(u'trac', ['Split'])

        # Adding unique constraint on 'Split', fields ['tag', 'time']
        db.create_unique(u'trac_split', ['tag_id', 'time'])

        # Adding model 'TimingSession'
        db.create_table(u'trac_timingsession', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('coach', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trac.Coach'])),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('stop_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('start_button_time', self.gf('django.db.models.fields.BigIntegerField')(null=True, blank=True)),
            ('use_registered_tags_only', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('private', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=2500, blank=True)),
            ('rest_time', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('track_size', self.gf('django.db.models.fields.IntegerField')(default=400, blank=True)),
            ('interval_distance', self.gf('django.db.models.fields.IntegerField')(default=200, blank=True)),
            ('interval_number', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('filter_choice', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'trac', ['TimingSession'])

        # Adding M2M table for field readers on 'TimingSession'
        m2m_table_name = db.shorten_name(u'trac_timingsession_readers')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('timingsession', models.ForeignKey(orm[u'trac.timingsession'], null=False)),
            ('reader', models.ForeignKey(orm[u'trac.reader'], null=False))
        ))
        db.create_unique(m2m_table_name, ['timingsession_id', 'reader_id'])

        # Adding M2M table for field splits on 'TimingSession'
        m2m_table_name = db.shorten_name(u'trac_timingsession_splits')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('timingsession', models.ForeignKey(orm[u'trac.timingsession'], null=False)),
            ('split', models.ForeignKey(orm[u'trac.split'], null=False))
        ))
        db.create_unique(m2m_table_name, ['timingsession_id', 'split_id'])

        # Adding M2M table for field registered_tags on 'TimingSession'
        m2m_table_name = db.shorten_name(u'trac_timingsession_registered_tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('timingsession', models.ForeignKey(orm[u'trac.timingsession'], null=False)),
            ('tag', models.ForeignKey(orm[u'trac.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['timingsession_id', 'tag_id'])

        # Adding model 'PerformanceRecord'
        db.create_table(u'trac_performancerecord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('distance', self.gf('django.db.models.fields.IntegerField')()),
            ('time', self.gf('django.db.models.fields.FloatField')()),
            ('interval', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('VO2', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('athlete', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trac.Athlete'], null=True)),
            ('coach', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['trac.Coach'], null=True)),
        ))
        db.send_create_signal(u'trac', ['PerformanceRecord'])


    def backwards(self, orm):
        # Removing unique constraint on 'Split', fields ['tag', 'time']
        db.delete_unique(u'trac_split', ['tag_id', 'time'])

        # Deleting model 'Coach'
        db.delete_table(u'trac_coach')

        # Deleting model 'Team'
        db.delete_table(u'trac_team')

        # Deleting model 'Athlete'
        db.delete_table(u'trac_athlete')

        # Deleting model 'Tag'
        db.delete_table(u'trac_tag')

        # Deleting model 'Reader'
        db.delete_table(u'trac_reader')

        # Deleting model 'Split'
        db.delete_table(u'trac_split')

        # Deleting model 'TimingSession'
        db.delete_table(u'trac_timingsession')

        # Removing M2M table for field readers on 'TimingSession'
        db.delete_table(db.shorten_name(u'trac_timingsession_readers'))

        # Removing M2M table for field splits on 'TimingSession'
        db.delete_table(db.shorten_name(u'trac_timingsession_splits'))

        # Removing M2M table for field registered_tags on 'TimingSession'
        db.delete_table(db.shorten_name(u'trac_timingsession_registered_tags'))

        # Deleting model 'PerformanceRecord'
        db.delete_table(u'trac_performancerecord')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'trac.athlete': {
            'Meta': {'object_name': 'Athlete'},
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['trac.Team']", 'null': 'True', 'blank': 'True'}),
            'tfrrs_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'year': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
        },
        u'trac.coach': {
            'Meta': {'object_name': 'Coach'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'trac.performancerecord': {
            'Meta': {'object_name': 'PerformanceRecord'},
            'VO2': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'athlete': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['trac.Athlete']", 'null': 'True'}),
            'coach': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['trac.Coach']", 'null': 'True'}),
            'distance': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'time': ('django.db.models.fields.FloatField', [], {})
        },
        u'trac.reader': {
            'Meta': {'object_name': 'Reader'},
            'coach': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['trac.Coach']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_str': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'trac.split': {
            'Meta': {'unique_together': "(('tag', 'time'),)", 'object_name': 'Split'},
            'athlete': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['trac.Athlete']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reader': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['trac.Reader']"}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['trac.Tag']"}),
            'time': ('django.db.models.fields.BigIntegerField', [], {})
        },
        u'trac.tag': {
            'Meta': {'object_name': 'Tag'},
            'athlete': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['trac.Athlete']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_str': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'trac.team': {
            'Meta': {'object_name': 'Team'},
            'coach': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['trac.Coach']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'tfrrs_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        u'trac.timingsession': {
            'Meta': {'object_name': 'TimingSession'},
            'coach': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['trac.Coach']"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'blank': 'True'}),
            'filter_choice': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval_distance': ('django.db.models.fields.IntegerField', [], {'default': '200', 'blank': 'True'}),
            'interval_number': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'readers': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['trac.Reader']", 'symmetrical': 'False'}),
            'registered_tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['trac.Tag']", 'symmetrical': 'False'}),
            'rest_time': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'splits': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['trac.Split']", 'symmetrical': 'False'}),
            'start_button_time': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'stop_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'track_size': ('django.db.models.fields.IntegerField', [], {'default': '400', 'blank': 'True'}),
            'use_registered_tags_only': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['trac']