import random
import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

import os.path
from .models import Census
from base import mods
from base.tests import BaseTestCase
from voting.models import *


class CensusTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.census = Census(voting_id=1, voter_id=1)
        self.census.save()

    def tearDown(self):
        super().tearDown()
        self.census = None

    def test_check_vote_permissions(self):
        response = self.client.get('/census/{}/?voter_id={}'.format(1, 2), format='json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), 'Invalid voter')

        response = self.client.get('/census/{}/?voter_id={}'.format(1, 1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Valid voter')

    def test_list_voting(self):
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/census/?voting_id={}'.format(1), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'voters': [1]})

    def test_add_new_voters_conflict(self):
        data = {'voting_id': 1, 'voters': [1]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 409)

    def test_add_new_voters(self):
        data = {'voting_id': 2, 'voters': [1,2,3,4]}
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.post('/census/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(data.get('voters')), Census.objects.count() - 1)

    def test_destroy_voter(self):
        data = {'voters': [1]}
        response = self.client.delete('/census/{}/'.format(1), data, format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, Census.objects.count())
        
    def test_import(self):
        #Creamos el usuario con privilegios de administrador
        admin = User(username='administrado')
        admin.set_password('1234567asd')
        admin.is_staff = True
        admin.save()

        # GET the import form
        self.client.force_login(admin)
        response = self.client.get('/census/importExcel/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'importarExcel.html')

        # POST the import form
        input_format = 'xlsfile'
        filename = os.path.join(
            os.path.dirname(__file__),
            'importar.xlsx')
        with open(filename, "rb") as f:
            data = {
                'xlsfile': f,
            }
            response = self.client.post('/census/voting/', data)
        self.assertEqual(response.status_code, 200)
        
    def test_ldap_check_votacion_pass(self):
        antes = Census.objects.count()

        #Guardamos al usuario a introducir que ya esta en el ldap
        u = User(username='curie')
        u.set_password('123')
        u.save()

        admin = User(username='administrado')
        admin.set_password('1234567asd')
        admin.is_staff = True
        admin.save()

        #Creación de la votación
        q = Question(desc='test question')
        q.save()
        v = Voting(name='titulo 1', desc='Descripcion1',question=q)
        v.save()

        #Hacemos la request
        
        self.client.force_login(admin)
        
        votacion = Voting.objects.all().filter(end_date__isnull=True)[0].id
        data = {'voting': votacion, 'urlLdap': 'ldap.forumsys.com:389', 'branch': 'ou=chemists,dc=example,dc=com', 'treeSufix': 'cn=read-only-admin,dc=example,dc=com','pwd': 'password'}
        response = self.client.post('/census/addLDAPcensusVotacion/', data)
        despues = Census.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(antes+1,despues)

    def test_ldap_check_votacion_wrong_login(self):

        antes = Census.objects.count()
        
        #Guardamos al usuario a introducir que ya esta en el ldap
        u = User(username='curie')
        u.set_password('123')
        u.save()

        admin = User(username='administrado')
        admin.set_password('1234567asd')
        admin.is_staff = True
        admin.save()

        #Creación de la votación
        q = Question(desc='test question')
        q.save()
        v = Voting(name='titulo 1', desc='Descripcion1',question=q)
        v.save()

        #Hacemos la request
        
        self.client.force_login(u)
        votacion = Voting.objects.all().filter(end_date__isnull=True)[0].id
        data = {'voting': votacion, 'urlLdap': 'ldap.forumsys.com:389', 'branch': 'ou=chemists,dc=example,dc=com', 'treeSufix': 'cn=read-only-admin,dc=example,dc=com','pwd': 'password'}
        response = self.client.post('/census/addLDAPcensusVotacion/', data)
        despues = Census.objects.count()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(antes,despues)


    
    def test_ldap_check_votacion_get(self):
        antes = Census.objects.count()
      
        u = User(username='curie')
        u.set_password('123')
        u.save()

        admin = User(username='administrado')
        admin.set_password('1234567asd')
        admin.is_staff = True
        admin.save()

        #Hacemos la request
        
        self.client.force_login(admin)
        response = self.client.get('/census/addLDAPcensusVotacion/')
        despues = Census.objects.count()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(antes,despues)



class ReuseCensusTest(BaseTestCase):
    def testReuse(self):
        response = self.client.get('/census/reuse/1/2/')    
        num_voters1=Census.objects.filter(voting_id=1).count()
        num_voters2=Census.objects.filter(voting_id=2).count()
        self.assertEquals(num_voters1, num_voters2)

class ExportCensusTest(BaseTestCase):
    def setUp(self):
        self.census = Census(voting_id=1, voter_id=1)
        self.census.save()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.census = None

    def testExportCsv(self):
        response = self.client.get('/census/export/csv/')
        self.assertEquals(response.get('Content-Type'), 'text/csv')
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="census.csv"')

    def testExportExcel(self):
        response = self.client.get('/census/export/xls/')
        self.assertEquals(response.get('Content-Type'), 'application/vnd.ms-excel')
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="census.xls"')
   
    def testExportJson(self):
        response = self.client.get('/census/export/json/')
        self.assertEquals(response.get('Content-Type'), 'application/json')
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="census.json"')
        
    def testExportError(self):
        response = self.client.get('/census/export/sdgsd')
        self.assertEquals(response.status_code, 301)


class ExportCensusByVoterTest(BaseTestCase):
    def setUp(self):
        self.census = Census(voting_id=1, voter_id=1)
        self.census.save()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.census = None


    def testExportByVoterCsv(self):
        response = self.client.get('/census/exportbyVoter/1/csv/')
        self.assertEquals(response.get('Content-Type'), 'text/csv')
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="census.csv"')


    def testExportByVoterExcel(self):
        response = self.client.get('/census/exportbyVoter/1/xls/')
        self.assertEquals(response.get('Content-Type'), 'application/vnd.ms-excel')
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="census.xls"')

    def testExportByVoterJson(self):
        response = self.client.get('/census/exportbyVoter/1/json/')
        self.assertEquals(response.get('Content-Type'), 'application/json')
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="census.json"')

    def testExportByVoterError(self):
        response = self.client.get('/census/exportbyVoter/1/asdasf')
        self.assertEquals(response.status_code, 301)

class ExportCensusByVotingTest(BaseTestCase):
    def setUp(self):
        self.census = Census(voting_id=1, voter_id=1)
        self.census.save()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.census = None


    def testExportByVotingCsv(self):
        response = self.client.get('/census/exportbyVoting/1/csv/')
        self.assertEquals(response.get('Content-Type'), 'text/csv')
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="census.csv"')


    def testExportByVotingExcel(self):
        response = self.client.get('/census/exportbyVoting/1/xls/')
        self.assertEquals(response.get('Content-Type'), 'application/vnd.ms-excel')
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="census.xls"')

    def testExportByVotingJson(self):
        response = self.client.get('/census/exportbyVoting/1/json/')
        self.assertEquals(response.get('Content-Type'), 'application/json')
        self.assertEquals(response.get('Content-Disposition'), 'attachment; filename="census.json"')

    def testExportByVotingrror(self):
        response = self.client.get('/census/exportbyVoting/1/asdasf')
        self.assertEquals(response.status_code, 301)
