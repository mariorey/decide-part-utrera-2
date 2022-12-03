import random
import datetime
import time
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

import os.path
from .models import Census
from voting.models import Voting, Question
from base.models import Auth
from base import mods
from base.tests import BaseTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from voting.models import *

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from django.utils import timezone

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

class ImportCensusTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.driver = webdriver.Chrome()
        options = webdriver.ChromeOptions()
        options.headless = False
        self.driver = webdriver.Chrome(options=options)
        self.vars = {}
        

    def tearDown(self):
        super().tearDown()
        self.driver.quit()

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
    

        
    def test_1_importLDAPtest_pass(self):
        self.driver.get("http://127.0.0.1:55257/admin/login/?next=/admin/")
        self.driver.set_window_size(1552, 840)
        self.driver.find_element(By.ID, "id_username").send_keys("decide")
        self.driver.find_element(By.ID, "id_password").send_keys("complexpassword")
        self.driver.find_element(By.CSS_SELECTOR, ".submit-row > input").click()
        self.driver.find_element(By.LINK_TEXT, "Questions").click()
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("¿Quién ganará?")
        self.driver.find_element(By.ID, "id_options-0-option").click()
        self.driver.find_element(By.ID, "id_options-0-option").send_keys("Sevilla")
        self.driver.find_element(By.ID, "id_options-1-option").click()
        self.driver.find_element(By.ID, "id_options-1-option").send_keys("Betis")
        self.driver.find_element(By.ID, "id_options-2-option").click()
        self.driver.find_element(By.ID, "id_options-2-option").send_keys("Empate")
        self.driver.find_element(By.ID, "id_options-0-number").click()
        self.driver.find_element(By.ID, "id_options-0-number").send_keys("1")
        self.driver.find_element(By.ID, "id_options-1-number").click()
        self.driver.find_element(By.ID, "id_options-1-number").send_keys("1")
        self.driver.find_element(By.ID, "id_options-2-number").click()
        self.driver.find_element(By.ID, "id_options-2-number").send_keys("1")
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.find_element(By.LINK_TEXT, "Voting").click()
        self.driver.find_element(By.LINK_TEXT, "Votings").click()
        self.driver.find_element(By.CSS_SELECTOR, ".addlink").click()
        self.driver.find_element(By.ID, "id_name").click()
        self.driver.find_element(By.ID, "id_name").send_keys("Betis o Sevilla")
        self.driver.find_element(By.ID, "id_desc").click()
        self.driver.find_element(By.ID, "id_desc").send_keys("Quien va a ganar")
        self.driver.find_element(By.ID, "id_question").click()
        dropdown = self.driver.find_element(By.ID, "id_question")
        dropdown.find_element(By.XPATH, "//option[. = '¿Quién ganará?']").click()
        dropdown = self.driver.find_element(By.ID, "id_auths")
        dropdown.find_element(By.XPATH, "//option[. = 'http://127.0.0.1:8000']").click()
        self.driver.find_element(By.NAME, "_save").click()
        self.driver.find_element(By.NAME, "_selected_action").click()
        self.driver.find_element(By.NAME, "action").click()
        dropdown = self.driver.find_element(By.NAME, "action")
        dropdown.find_element(By.XPATH, "//option[. = 'Start']").click()
        self.driver.find_element(By.NAME, "index").click()
        self.driver.get("http://127.0.0.1:55257/census/voting/")
        self.driver.find_element(By.LINK_TEXT, "Importar censo desde LDAP").click()
        self.driver.find_element(By.ID, "id_voting").click()
        dropdown = self.driver.find_element(By.ID, "id_voting")
        dropdown.find_element(By.XPATH, "//option[. = 'Betis o Sevilla']").click()
        self.driver.find_element(By.ID, "id_urlLdap").click()
        self.driver.find_element(By.ID, "id_urlLdap").send_keys("ldap.forumsys.com:389")
        self.driver.find_element(By.ID, "id_treeSufix").click()
        self.driver.find_element(By.ID, "id_treeSufix").send_keys("cn=read-only-admin,dc=example,dc=com")
        self.driver.find_element(By.ID, "id_branch").click()
        self.driver.find_element(By.ID, "id_branch").send_keys("ou=chemists,dc=example,dc=com")
        self.driver.find_element(By.ID, "id_pwd").click()
        self.driver.find_element(By.ID, "id_pwd").send_keys("password")
        self.driver.find_element(By.CSS_SELECTOR, "strong").click()
        self.driver.find_element(By.LINK_TEXT, "Betis o Sevilla").click()
        assert self.driver.find_element(By.XPATH, "//tbody/tr[1]/th").text == "curie"
        assert self.driver.find_element(By.XPATH, "//tbody/tr[2]/th").text == "boyle"
        assert self.driver.find_element(By.XPATH, "//tbody/tr[3]/th").text == "nobel"
        assert self.driver.find_element(By.XPATH, "//tbody/tr[4]/th").text == "pasteur"
        self.driver.get("http://127.0.0.1:55257/admin/")
        self.driver.find_element(By.CSS_SELECTOR, "a:nth-child(4)").click()
    


    def test_2_importLDAPtest_fail(self):
        self.driver.get("http://127.0.0.1:55257/admin/login/?next=/admin/")
        self.driver.set_window_size(1552, 840)
        self.driver.find_element(By.ID, "id_username").send_keys("decide")
        self.driver.find_element(By.ID, "id_password").send_keys("complexpassword")
        self.driver.find_element(By.CSS_SELECTOR, ".submit-row > input").click()
        self.driver.get("http://127.0.0.1:55257/census/voting/")
        self.driver.find_element(By.LINK_TEXT, "Importar censo desde LDAP").click()
        dropdown = self.driver.find_element(By.ID, "id_voting")
        dropdown.find_element(By.XPATH, "//option[. = 'Betis o Sevilla']").click()
        element = self.driver.find_element(By.ID, "id_voting")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().perform()
        element = self.driver.find_element(By.ID, "id_voting")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        element = self.driver.find_element(By.ID, "id_voting")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).release().perform()
        self.driver.find_element(By.ID, "id_urlLdap").click()
        self.driver.find_element(By.ID, "id_urlLdap").send_keys("ldap.forumsys.com:389")
        self.driver.find_element(By.ID, "id_treeSufix").click()
        self.driver.find_element(By.ID, "id_treeSufix").send_keys("cn=read-only-admin,dc=example,dc=com")
        self.driver.find_element(By.ID, "id_branch").click()
        self.driver.find_element(By.ID, "id_branch").send_keys("ou=chemists,dc=example,dc=com")
        self.driver.find_element(By.ID, "id_pwd").click()
        self.driver.find_element(By.ID, "id_pwd").send_keys("password")
        self.driver.find_element(By.CSS_SELECTOR, "strong").click()
        assert self.driver.find_element(By.CSS_SELECTOR, ".alert-danger:nth-child(1)").text == "El usuario curie ya se encuentra en la base de datos"
        assert self.driver.find_element(By.CSS_SELECTOR, ".alert-danger:nth-child(2)").text == "El usuario boyle ya se encuentra en la base de datos"
        assert self.driver.find_element(By.CSS_SELECTOR, ".alert-danger:nth-child(3)").text == "El usuario nobel ya se encuentra en la base de datos"
        assert self.driver.find_element(By.CSS_SELECTOR, ".alert-danger:nth-child(4)").text == "El usuario pasteur ya se encuentra en la base de datos"
    



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


class AdministratorViewCensusTest(StaticLiveServerTestCase):
    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = False
        self.driver = webdriver.Chrome(options=options)

    def teardown_method(self, method):
        self.driver.quit()
  
    def test_show_all(self):
        censo1 = Census(voting_id=1, voter_id=1)
        censo1.save()
        censo2 = Census(voting_id=2, voter_id=1)
        censo2.save()
        censo3 = Census(voting_id=3, voter_id=1)
        censo3.save()
        self.driver.get(f'{self.live_server_url}/census/showAll')
        censo1_voter_id = self.driver.find_element(By.ID, "voter_"+str(censo1.id)).text
        self.assertTrue(censo1_voter_id, str(censo1.voter_id))
        censo1_voting_id = self.driver.find_element(By.ID, "voting_"+str(censo1.id)).text
        self.assertTrue(censo1_voting_id, str(censo1.voting_id))
        censo2_voter_id = self.driver.find_element(By.ID, "voting_"+str(censo2.id)).text
        self.assertTrue(censo2_voter_id, str(censo2.voter_id))
        censo2_voting_id = self.driver.find_element(By.ID, "voting_"+str(censo2.id)).text
        self.assertTrue(censo2_voting_id, str(censo2.voting_id))
        censo3_voter_id = self.driver.find_element(By.ID, "voter_"+str(censo3.id)).text
        self.assertTrue(censo3_voter_id, str(censo3.voter_id))
        censo3_voting_id = self.driver.find_element(By.ID, "voting_"+str(censo3.id)).text
        self.assertTrue(censo3_voting_id, str(censo3.voting_id))

    def test_show_all_votings(self):
        self.driver.get(f'{self.live_server_url}/census/login')
        username = self.driver.find_element_by_name("username")
        password = self.driver.find_element_by_name("password")
        submit = self.driver.find_element_by_name("submit")
        username.send_keys('admin')
        password.send_keys('qwerty')
        submit.click()
        question = Question(desc="Es un test")
        question.save()
        auth = Auth(name="Test",url="Test")
        auth.save()
        voting1 = Voting(name="Test",desc="Es un test",question = question)
        voting1.save()
        voting1.auths.add(auth)
        voting2 = Voting(name="Test",desc="Es un test",question = question,start_date=timezone.now(),end_date=timezone.now())
        voting2.save()
        voting2.auths.add(auth)
        voter1 = User(username='voter1')
        voter1.set_password('1234567asd')
        voter1.save()
        voter2 = User(username='voter2')
        voter2.set_password('1234567asd')
        voter2.save()
        voter3 = User(username='voter3')
        voter3.set_password('1234567asd')
        voter3.save()
        censo1 = Census(voting_id=voting1.id, voter_id=voter1.id)
        censo1.save()
        censo2 = Census(voting_id=voting1.id, voter_id=voter2.id)
        censo2.save()
        censo3 = Census(voting_id=voting1.id, voter_id=voter3.id)
        censo3.save()
        self.driver.get(f'{self.live_server_url}/census/voting')
        voting1_name = self.driver.find_element(By.ID, "name_"+str(voting1.id)).text
        self.assertTrue(voting1_name, voting1.name)
        voting1_desc = self.driver.find_element(By.ID, "desc_"+str(voting1.id)).text
        self.assertTrue(voting1_desc, voting1.desc)
        voting1_date = self.driver.find_element(By.ID, "date_"+str(voting1.id)).text
        self.assertTrue(voting1_date, "Votation in progress")
        voting2_name = self.driver.find_element(By.ID, "name_"+str(voting2.id)).text
        self.assertTrue(voting2_name, voting2.name)
        voting2_desc = self.driver.find_element(By.ID, "desc_"+str(voting2.id)).text
        self.assertTrue(voting2_desc, voting2.desc)
        voting2_date = self.driver.find_element(By.ID, "date_"+str(voting2.id)).text
        self.assertTrue(voting2_date, "from "+str(voting2.start_date)+" to "+str(voting2.end_date))

        self.driver.get(f'{self.live_server_url}/census/voting/%s' %(voting1.id))

        voter1_username = self.driver.find_element(By.ID, "username_"+str(voter1.id)).text
        self.assertTrue(voter1_username, voter1.username)
        voter2_username = self.driver.find_element(By.ID, "username_"+str(voter2.id)).text
        self.assertTrue(voter2_username, voter2.username)
        voter3_username = self.driver.find_element(By.ID, "username_"+str(voter3.id)).text
        self.assertTrue(voter3_username, voter3.username)
        delete = self.driver.find_element(By.ID, "delete_"+str(voter1.id))
        delete.click()
        census_count = Census.objects.filter(voting_id = voting1.id).count()
        self.assertEquals(census_count,2)

        self.driver.find_element(By.NAME,"add").click()
        self.driver.find_element(By.XPATH,"//*[@id='id_voters']/option[text()='"+str(voter1.username)+"']").click()
        self.driver.find_element(By.NAME,"button").click()
        time.sleep(5)
        voter1_username = self.driver.find_element(By.ID, "username_"+str(voter1.id)).text
        self.assertTrue(voter1_username, voter1.username)



class login(StaticLiveServerTestCase):
    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = False
        self.driver = webdriver.Chrome(options=options)

    def teardown_method(self, method):
        self.driver.quit()
  
    def test_login(self):
        self.driver.get(f'{self.live_server_url}/census/login')
        username = self.driver.find_element_by_name("username")
        password = self.driver.find_element_by_name("password")
        time.sleep(5)
        submit = self.driver.find_element_by_name("submit")

        username.send_keys('admin')
        password.send_keys('qwerty')
        time.sleep(5)
        submit.click()
        time.sleep(5)
        assert 'Bienvenido,' in self.driver.page_source

    def test_negativo(self):
        self.driver.get(f'{self.live_server_url}/census/login')
        username = self.driver.find_element_by_name("username")
        password = self.driver.find_element_by_name("password")
        time.sleep(5)
        submit = self.driver.find_element_by_name("submit")

        username.send_keys('admin')
        password.send_keys('qwert')
        time.sleep(5)
        submit.click()
        time.sleep(5)
        assert 'Please enter a correct username and password. Note that both fields may be case-sensitive.' in self.driver.page_source

        
class logout(StaticLiveServerTestCase):
    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = False
        self.driver = webdriver.Chrome(options=options)

    def teardown_method(self, method):
        self.driver.quit()
  
    def test_logout(self):
        self.driver.get(f'{self.live_server_url}/census/login')
        username = self.driver.find_element_by_name("username")
        password = self.driver.find_element_by_name("password")
        time.sleep(5)
        submit = self.driver.find_element_by_name("submit")

        username.send_keys('admin')
        password.send_keys('qwerty')
        time.sleep(5)
        submit.click()
        time.sleep(5)
        logout = self.driver.find_element_by_name("logout")
        logout.click()
        assert 'Iniciar Sesión' in self.driver.page_source

class register(StaticLiveServerTestCase):
    def setUp(self):
        self.base = BaseTestCase()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = False
        self.driver = webdriver.Chrome(options=options)

    def teardown_method(self, method):
        self.driver.quit()
  
    def test_register(self):
    
        self.driver.get(f'{self.live_server_url}/census/register')
        username = self.driver.find_element_by_name("username")
        email = self.driver.find_element_by_name("email")
        password1 = self.driver.find_element_by_name("password1")
        password2= self.driver.find_element_by_name("password2")
        submit = self.driver.find_element_by_name("submit1")

        username.send_keys('CharlesDarwin')
        email.send_keys('charles@gmail.com')
        password1.send_keys('evolutionisalie1')
        password2.send_keys('evolutionisalie1',Keys.ENTER)
        user = User.objects.get(username='CharlesDarwin')
        self.assertEquals(user.username,'CharlesDarwin')
        self.assertEquals(user.email,'charles@gmail.com')
        assert 'se ha registrado correctamente' in self.driver.page_source
        

    def test_register_negative(self):
        self.driver.get(f'{self.live_server_url}/census/register')
        username = self.driver.find_element_by_name("username")
        email = self.driver.find_element_by_name("email")
        password1 = self.driver.find_element_by_name("password1")
        password2= self.driver.find_element_by_name("password2")
        submit = self.driver.find_element_by_name("submit1")

        username.send_keys('Charles Darwin')
        email.send_keys('a')
        password1.send_keys('evolutionisalie1')
        password2.send_keys('evolutionisalie1',Keys.ENTER)
        assert 'se ha registrado correctamente' not in self.driver.page_source

