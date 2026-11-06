"""Regression suite for an advisory research packet validator (no LLM)."""
from copy import deepcopy
from pathlib import Path
import json
import unittest
from workcoord_lab.research_quality import (FAMILIES, InvalidResearchPacket,
                                             evaluate_research)
from workcoord_lab.research_quality_suite import run_suite

CASES = Path(__file__).resolve().parents[1]/'examples'/'research-quality-cases-v0.json'


def load_cases():
    data=json.loads(CASES.read_text(encoding='utf-8'))
    assert data['schema']=='workcoord.research-case-catalog/v0'
    return data['cases']


class ResearchAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases={r['case_id']:r for r in load_cases()}

    def run_case(self, key):
        return evaluate_research(deepcopy(self.cases[key]['packet']))

    def assert_issue(self,key,code):
        result=self.run_case(key)
        self.assertTrue(any(code in items for items in result['issues'].values()),
                        msg=f'{key}: {code} absent: {result["issues"]}')
        return result

    def test_suite_receipt_covers_all_cases_with_pinned_hash(self):
        receipt=run_suite()
        self.assertEqual(receipt['case_count'],14)
        self.assertEqual(receipt['passed_fixture_expectations'],14)
        self.assertEqual(len(receipt['catalog_sha256']),64)
        self.assertTrue(receipt['no_empirical_efficacy_claim'])
        self.assertEqual(json.dumps(receipt,sort_keys=True),
                         json.dumps(run_suite(),sort_keys=True))

    def test_catalog_contains_simple_positive_and_negative_controls(self):
        self.assertEqual(len(self.cases),14)
        self.assertEqual(len(self.cases),len(set(self.cases)))
        self.assertTrue({'RQ01','RQ03','RQ06','RQ07','RQ08','RQ09','RQ11'}<=set(self.cases))

    def test_all_examples_match_published_development_expectations(self):
        for key,row in self.cases.items():
            with self.subTest(key=key):
                result=evaluate_research(row['packet'])
                self.assertEqual(result['status'],row['expected_status'])
                actual={v for group in result['issues'].values() for v in group}
                self.assertTrue(set(row['expected_issue_codes']).issubset(actual))
                self.assertEqual(result['execution_authority'],'NONE')
                self.assertEqual(result['knowledge_promotion'],'NOT_GRANTED')
                self.assertIs(result['verified_causal_claim'],False)
                self.assertEqual(result['observed_productivity_gain'],'NOT_MEASURED')

    def test_quick_does_not_require_hypothesis_grid_or_controls(self):
        r=self.run_case('RQ01')
        self.assertEqual(r['status'],'DESIGN_ADMISSIBLE')
        self.assertEqual(r['issue_count'],0)

    def test_structured_falsifiable_study_can_be_proposed(self):
        r=self.run_case('RQ02')
        self.assertEqual(r['status'],'DESIGN_ADMISSIBLE')
        self.assertEqual(r['eligible_evidence_ids'],['queue-observation'])

    def test_late_outcome_freeze_blocks_admission(self):
        self.assert_issue('RQ03','PLAN_NOT_FROZEN_BEFORE_OUTCOME')

    def test_postdecision_source_available_time_is_caught(self):
        self.assert_issue('RQ04','SOURCE_NOT_AVAILABLE_AT_DECISION')

    def test_duplicate_origin_does_not_count_as_two_independent_sources(self):
        r=self.assert_issue('RQ05','NO_INDEPENDENT_ORIGIN_GROUPS_DECLARED')
        self.assertEqual(r['declared_origin_groups'],['queue-simulator'])

    def test_critical_design_is_not_a_verified_decision(self):
        r=self.run_case('RQ06')
        self.assertEqual(r['status'],'REQUIRES_EXTERNAL_REVIEW')
        self.assertEqual(len(r['declared_origin_groups']),2)
        self.assertEqual(r['execution_authority'],'NONE')

    def test_unjustified_proxy_metric_blocks_admission(self):
        self.assert_issue('RQ07','MEASURE_DOES_NOT_ESTABLISH_TARGET')

    def test_self_asserted_validation_never_passes(self):
        self.assert_issue('RQ08','CANNOT_PROMOTE_TO_TESTED_OR_VALIDATED_FROM_DECLARATIONS')

    def test_missing_negative_control_detected(self):
        self.assert_issue('RQ09','NEGATIVE_CONTROL_NOT_DEFINED')

    def test_early_outcome_freeze_allows_proposed_analysis_only(self):
        r=self.run_case('RQ10')
        self.assertEqual(r['status'],'DESIGN_ADMISSIBLE')
        self.assertIs(r['verified_causal_claim'],False)

    def test_stale_historical_source_never_promoted_as_current(self):
        self.assert_issue('RQ11','CURRENT_CONCLUSION_USES_STALE_OR_HISTORICAL_SOURCE')
        self.assert_issue('RQ12','NO_CURRENT_ADMISSIBLE_OBSERVATION')

    def test_read_after_decision_is_not_equivalent_to_observation_time(self):
        self.assert_issue('RQ13','SOURCE_NOT_AVAILABLE_AT_DECISION')

    def test_hypothesis_requires_actual_falsifier(self):
        self.assert_issue('RQ14','HYPOTHESIS_WITHOUT_FALSIFIER')

    def test_missing_current_source_blocks_observed_promotion(self):
        p=deepcopy(self.cases['RQ12']['packet'])
        p['requested_knowledge_state']='OBSERVED'
        r=evaluate_research(p)
        self.assertIn('OBSERVED_STATE_REQUIRES_CURRENT_EVIDENCE',r['issues']['claim_boundary'])

    def test_quick_with_critical_fields_does_not_gain_authority(self):
        p=deepcopy(self.cases['RQ06']['packet'])
        p['risk']='QUICK'
        r=evaluate_research(p)
        self.assertEqual(r['status'],'DESIGN_ADMISSIBLE')
        self.assertEqual(r['execution_authority'],'NONE')

    def test_wrong_revision_rejected_even_with_multiple_supporting_reads(self):
        p=deepcopy(self.cases['RQ06']['packet'])
        p['evidence'][0]['revision']='fictional-r0'
        r=evaluate_research(p)
        self.assertIn('CURRENT_CONCLUSION_USES_STALE_OR_HISTORICAL_SOURCE',r['issues']['source_integrity'])

    def test_independent_groups_are_only_declarations(self):
        self.assertIn('self-declared',self.run_case('RQ06')['explanation'])

    def test_repeated_ids_are_rejected(self):
        p=deepcopy(self.cases['RQ05']['packet'])
        p['evidence'][1]['id']=p['evidence'][0]['id']
        with self.assertRaises(InvalidResearchPacket):
            evaluate_research(p)

    def test_invalid_truthy_values_cannot_disable_outcome_freeze(self):
        p=deepcopy(self.cases['RQ03']['packet'])
        for value in (0,1,None,'false',[],{}):
            with self.subTest(value=value):
                p['evaluation']['outcome_bearing']=value
                with self.assertRaises(InvalidResearchPacket):
                    evaluate_research(p)

    def test_timestamps_must_be_timezone_aware(self):
        p=deepcopy(self.cases['RQ02']['packet'])
        p['evidence'][0]['available_at']='2026-08-11T10:01:00'
        with self.assertRaises(InvalidResearchPacket):
            evaluate_research(p)

    def test_nonchronological_observation_availability_rejected(self):
        p=deepcopy(self.cases['RQ02']['packet'])
        p['evidence'][0]['observed_at']='2026-08-11T10:05:00Z'
        r=evaluate_research(p)
        self.assertIn('INVALID_OBSERVATION_AVAILABILITY_READ_ORDER',r['issues']['chronology'])

    def test_missing_source_fields_invalid_not_successful_hold(self):
        p=deepcopy(self.cases['RQ02']['packet'])
        del p['source']['revision']
        with self.assertRaises(InvalidResearchPacket):
            evaluate_research(p)

    def test_enums_fail_closed_on_unhashable_values(self):
        for field in ('risk','requested_knowledge_state'):
            p=deepcopy(self.cases['RQ02']['packet'])
            p[field]=['malformed']
            with self.subTest(field=field), self.assertRaises(InvalidResearchPacket):
                evaluate_research(p)
        p=deepcopy(self.cases['RQ02']['packet'])
        p['evidence'][0]['source_class']={}
        with self.assertRaises(InvalidResearchPacket):
            evaluate_research(p)

    def test_unhashable_evidence_refs_are_rejected(self):
        p=deepcopy(self.cases['RQ02']['packet'])
        p['hypotheses'][0]['evidence_ids']=[['x']]
        with self.assertRaises(InvalidResearchPacket):
            evaluate_research(p)

    def test_removal_of_falsifier_and_controls_is_detected(self):
        p=deepcopy(self.cases['RQ02']['packet'])
        p['hypotheses'][0]['falsifier']=''
        p['controls']['negative_control']=''
        result=evaluate_research(p)
        self.assertIn('HYPOTHESIS_WITHOUT_FALSIFIER',result['issues']['alternative_tests'])
        self.assertIn('NEGATIVE_CONTROL_NOT_DEFINED',result['issues']['alternative_tests'])

    def test_no_gold_label_is_used_by_evaluator(self):
        p=deepcopy(self.cases['RQ02']['packet'])
        a=evaluate_research(p)
        p['private_true_cause']='opposite-unseen-outcome'
        self.assertEqual(a,evaluate_research(p))

    def test_output_is_deterministic_and_does_not_expose_source_text(self):
        p=deepcopy(self.cases['RQ02']['packet'])
        self.assertEqual(json.dumps(evaluate_research(p),sort_keys=True),
                         json.dumps(evaluate_research(p),sort_keys=True))
        self.assertNotIn(p['evidence'][0]['finding'],repr(evaluate_research(p)))

    def test_declared_scientific_families_are_present(self):
        self.assertEqual(len(FAMILIES),8)
        self.assertIn('outcome_peeking',FAMILIES)

if __name__=='__main__':
    unittest.main()
