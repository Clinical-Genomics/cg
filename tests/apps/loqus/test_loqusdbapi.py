# import subprocess
#
# from cg.apps.loqus import LoqusdbAPI
#
# def test_instatiate(loqus_config):
#     """Test to instantiate a loqusdb api"""
#     ## GIVEN a loqusdb api with some configs
#
#     ## WHEN instantiating a loqusdb api
#     loqusdb = LoqusdbAPI(loqus_config)
#
#     ## THEN assert that the adapter was properly instantiated
#     assert loqusdb.uri == loqus_config['loqusdb']['database']
#     assert loqusdb.db_name == loqus_config['loqusdb']['database_name']
#     assert loqusdb.loqusdb_binary == loqus_config['loqusdb']['binary']
#
# def test_get_case(loqusdbapi, mocker):
#     """Test to get a case via the api"""
#     ## GIVEN a loqusdb api
#     case_id = 'a_case'
#     ## WHEN fetching a case with the adapter
#     mocker.patch.object(subprocess, 'check_output')
#     subprocess.check_output.return_value = b'[{"_id": "a_case"}]'
#     case_obj = loqusdbapi.get_case(case_id)
#     ## THEN assert that the correct case id is returned
#     assert case_obj['_id'] == case_id
#
# def test_get_case_non_existing(loqusdbapi, mocker):
#     """Test to get a case via the api"""
#     ## GIVEN a loqusdb api
#     case_id = 'a_case'
#     ## WHEN fetching a case with the adapter
#     mocker.patch.object(subprocess, 'check_output')
#     subprocess.check_output.side_effect = subprocess.CalledProcessError(1,'error')
#     case_obj = loqusdbapi.get_case(case_id)
#
#     ## THEN assert None is returned
#     assert case_obj == None
#
# def test_load(loqusdbapi, mocker):
#     """Test to load a case"""
#     ## GIVEN a loqusdb api and some info about a case
#     family_id = 'test'
#     ped_path = 'a ped path'
#     vcf_path = 'a vcf path'
#
#     ## WHEN loading the case to loqus with the api
#     mocker.patch.object(subprocess, 'check_output')
#     subprocess.check_output.return_value = (b'2018-11-29 08:41:38 130-229-8-20-dhcp.local '
#     b'mongo_adapter.client[77135] INFO Connecting to uri:mongodb://None:None@localhost:27017\n'
#     b'2018-11-29 08:41:38 130-229-8-20-dhcp.local mongo_adapter.client[77135] INFO Connection '
#     b'established\n2018-11-29 08:41:38 130-229-8-20-dhcp.local mongo_adapter.adapter[77135] INFO'
#     b' Use database loqusdb\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.utils.vcf[77135]'
#     b' INFO Check if vcf is on correct format...\n2018-11-29 08:41:38 130-229-8-20-dhcp.local'
#     b' loqusdb.utils.vcf[77135] INFO Vcf file /Users/mansmagnusson/Projects/loqusdb/tests/fixtures'
#     b'/test.vcf.gz looks fine\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.utils.vcf[77135]'
#     b' INFO Nr of variants in vcf: 15\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.utils.'
#     b'vcf[77135] INFO Type of variants in vcf: snv\nInserting variants\n2018-11-29 08:41:38 130-22'
#     b'9-8-20-dhcp.local loqusdb.utils.load[77135] INFO Inserted 15 variants of type snv\n2018-11-2'
#     b'9 08:41:38 130-229-8-20-dhcp.local loqusdb.commands.load[77135] INFO Nr variants inserted: '
#     b'15\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.commands.load[77135] INFO Time to '
#     b'insert variants: 0:00:00.012648\n2018-11-29 08:41:38 130-229-8-20-dhcp.local loqusdb.plugins.'
#     b'mongo.adapter[77135] INFO All indexes exists\n')
#
#     data = loqusdbapi.load(family_id, ped_path, vcf_path)
#
#     ## THEN assert that the number of variants is 15
#
#     assert data['variants'] == 15
#
