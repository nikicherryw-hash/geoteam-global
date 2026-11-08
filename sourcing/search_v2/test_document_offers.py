import json
import unittest
from .document_offers import document_parts, validate_document_output


class DocumentOfferTests(unittest.TestCase):
    def envelope(self):
        candidates = [{'url':'https://seller.example/'+part,'model':'Siemens '+part,
                       'part_number':part,'seller':'Private seller','price':10,'currency':'EUR',
                       'availability_claim':'unknown','condition':'NEW'}
                      for part in ['5SY6106-7','5SL6106-6','5SY6106-8']]
        report = {'resolved_product':'List of Siemens components','product':{},'candidates':candidates,'warnings':[]}
        return {'output':[{'type':'web_search_call','action':{'sources':[{'url':c['url']} for c in candidates]}},
                          {'type':'message','content':[{'type':'output_text','text':json.dumps(report)}]}]}

    def test_each_row_keeps_its_own_exact_offers(self):
        result = validate_document_output(self.envelope(),'List of 17 Siemens components','ru','5SY6106-7\t5\n5SL6106-6\t2')
        self.assertEqual([x['part_number'] for x in result['offers']], ['5SY6106-7','5SL6106-6'])
        self.assertNotIn('source_url', str(result['offers']))
        self.assertNotIn('Private seller', str(result['offers']))
        self.assertEqual(len({x['public_offer_id'] for x in result['offers']}),2)

    def test_uncited_listing_still_rejected(self):
        data=self.envelope();data['output'][0]['action']['sources']=[]
        self.assertEqual(validate_document_output(data,'List','en','5SY6106-7 5SL6106-6')['offers'],[])

    def test_single_document_part_is_not_matched_to_document_title(self):
        result=validate_document_output(self.envelope(),'Excel procurement document','ru','5SY6106-7\t5')
        self.assertEqual([x['part_number'] for x in result['offers']],['5SY6106-7'])

    def test_document_manufacturer_must_match_listing(self):
        data=self.envelope();report=json.loads(data['output'][1]['content'][0]['text'])
        report['product']={'manufacturer':'Siemens'}
        report['candidates'][0]['model']='ABB 5SY6106-7'
        data['output'][1]['content'][0]['text']=json.dumps(report)
        result=validate_document_output(data,'List','ru','Siemens\n5SY6106-7\n5SL6106-6')
        self.assertEqual([x['part_number'] for x in result['offers']],['5SL6106-6'])

    def test_document_codes_are_not_silently_truncated(self):
        parts=' '.join('5SY61%02d-7'%i for i in range(17))
        self.assertEqual(len(document_parts(parts)),17)
        with self.assertRaises(ValueError):
            document_parts(parts,maximum=10)

    def test_document_accepts_one_hundred_positions_and_rejects_one_more(self):
        parts=' '.join('5SY61%03d-7'%i for i in range(100))
        self.assertEqual(len(document_parts(parts)),100)
        with self.assertRaises(ValueError):
            document_parts(parts + ' 5SY61999-7')

    def test_filename_style_excel_cells_keep_part_numbers(self):
        text = 'Автоматический выключатель_5SY6106-7_Siemens\t5 шт\n' \
               'Автоматический выключатель_5SL6106-6_Siemens\t2 шт'
        self.assertEqual(document_parts(text), ['5SY6106-7', '5SL6106-6'])

    def test_conflicting_declared_part_is_rejected(self):
        data=self.envelope();report=json.loads(data['output'][1]['content'][0]['text']);report['candidates'][0]['part_number']='5SY6106-8'
        data['output'][1]['content'][0]['text']=json.dumps(report)
        result=validate_document_output(data,'List','ru','5SY6106-7 5SL6106-6')
        self.assertEqual([x['part_number'] for x in result['offers']],['5SL6106-6'])
