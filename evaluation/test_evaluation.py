"""Explicitly synthetic unit fixtures; never pilot or research evidence."""
import csv
from pathlib import Path
import tempfile
import unittest
from evaluation.run import recommender,fit_text,csat,pending,validate_ratings,bertscore,warm_hybrid
from unittest.mock import patch
class EvaluationTests(unittest.TestCase):
    def file(self,root,name,rows):
        path=Path(root)/name
        with path.open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
        return path
    def test_group_split_baseline_same_holdout_and_no_user_leakage(self):
        with tempfile.TemporaryDirectory() as root:
            rows=[dict(user_id=f'synthetic-{u}',item_id=f'item-{i}',rating=1+(u+i)%5,profile_text='python communication',item_text=f'python lesson topic{i}') for u in range(8) for i in range(3)]
            report=recommender(self.file(root,'synthetic.csv',rows),folds=5)
            comparisons=[report['comparison']]+report['cross_validation']['folds']
            for result in comparisons:
                self.assertFalse(set(result['train_users'])&set(result['test_users']))
                self.assertEqual(result['test_count'],len(result['holdout_hashes']))
                self.assertEqual(set(result['model']),set(result['item_mean_baseline']))
                self.assertGreaterEqual(result['model']['mae'],0)
    def test_text_fit_never_sees_heldout_only_terms(self):
        fitted=fit_text([{'profile_text':'python','item_text':'communication'}])
        self.assertNotIn('holdoutsecret',fitted.vocabulary_)
        self.assertEqual(fitted.transform(['holdoutsecret']).nnz,0)
    def test_empty_profile_and_item_text_preserve_statistical_baseline_evaluation(self):
        with tempfile.TemporaryDirectory() as root:
            rows=[dict(user_id=f'synthetic-{u}',item_id=f'item-{i}',rating=1+(u+i)%5,profile_text='',item_text='') for u in range(6) for i in range(2)]
            report=recommender(self.file(root,'empty-features.csv',rows),folds=5)
            self.assertEqual(report['comparison']['vocabulary_size'],0)
            self.assertGreaterEqual(report['comparison']['model']['rmse'],0)
    def test_missing_ratings_are_rejected_not_converted_to_zero(self):
        for rating in ('',0,6,'NaN'):
            with self.assertRaises((ValueError,TypeError)):validate_ratings([dict(user_id='synthetic',item_id='item',rating=rating,profile_text='x',item_text='y')])
    def test_no_inputs_produce_no_measured_metrics(self):
        self.assertEqual(recommender(None)['status'],'not_measured')
        self.assertIsNone(recommender(None)['metrics'])
        self.assertIsNone(csat(None)['sample_count'])
    def test_hybrid_five_folds_are_chronological_and_use_common_holdouts(self):
        from evaluation.run import hybrid_cross_validation
        with tempfile.TemporaryDirectory() as root:
            rows=[dict(user_id=f'synthetic-{u}',item_id=f'item-{(i if i<2 else 2+(i-2+3*u)%26)}',rating=1+(u+i)%5,
                       profile_text='python communication',item_text=f'python topic{(i if i<2 else 2+(i-2+3*u)%26)}',
                       occurred_at=f'2026-10-{i+1:02d}T00:00:00+00:00') for u in range(6) for i in range(28)]
            report=hybrid_cross_validation(self.file(root,'synthetic-folds.csv',rows),folds=5)
            self.assertEqual(report['status'],'measured_offline')
            self.assertEqual(len(report['folds']),5)
            for fold in report['folds']:
                self.assertLess(fold['train_end'],fold['validation_start'])
                self.assertLess(fold['validation_end'],fold['test_start'])
                self.assertEqual(fold['test_count'],len(fold['comparison']['holdout_hashes']))
                self.assertGreater(fold['comparison']['collaborative_covered_test_count'],0)
                self.assertEqual(set(fold['comparison']['model']),{'mae','rmse'})
            self.assertEqual(report['model_version'],'hybrid-v2')
            self.assertIsNone(hybrid_cross_validation(None)['metrics'])
    def test_hybrid_evaluation_selection_and_vocabulary_do_not_see_future_labels_or_text(self):
        from evaluation.run import hybrid_cross_validation
        with tempfile.TemporaryDirectory() as root:
            rows=[dict(user_id=f'synthetic-{u}',item_id=f'item-{(i if i<2 else 2+(i-2+3*u)%26)}',rating=1+(u+i)%5,
                       profile_text='python',item_text='python communication',occurred_at=f'2026-10-{i+1:02d}T00:00:00+00:00')
                  for u in range(6) for i in range(28)]
            first=hybrid_cross_validation(self.file(root,'base.csv',rows))
            for row in rows:
                if row['occurred_at']>='2026-10-09':
                    row['rating']=6-row['rating'];row['profile_text']='futuresecret'
            changed=hybrid_cross_validation(self.file(root,'changed.csv',rows))
            self.assertEqual(first['folds'][0]['selected_alpha'],changed['folds'][0]['selected_alpha'])
            self.assertEqual(first['folds'][0]['validation_metrics'],changed['folds'][0]['validation_metrics'])
    def test_synthetic_csat_distribution_and_duplicate_rejection(self):
        with tempfile.TemporaryDirectory() as root:
            rows=[dict(participant_id='synthetic-a',rating=4),dict(participant_id='synthetic-b',rating=2)]
            report=csat(self.file(root,'synthetic-csat.csv',rows));self.assertEqual(report['sample_count'],2);self.assertEqual(report['metrics']['mean'],3)
            rows[1]['participant_id']='synthetic-a'
            with self.assertRaises(ValueError):csat(self.file(root,'duplicates.csv',rows))
    def test_full_pipeline_never_fits_heldout_user_text(self):
        with tempfile.TemporaryDirectory() as root:
            rows=[dict(user_id=f'synthetic-{u}',item_id=f'item-{i}',rating=1+(u+i)%5,profile_text=f'python onlyuser{u}',item_text=f'python topic{i}') for u in range(8) for i in range(2)]
            fitted=[]
            def spy(train):
                model=fit_text(train);fitted.append((set(r['user_id'] for r in train),model));return model
            with patch('evaluation.run.fit_text',side_effect=spy):
                report=recommender(self.file(root,'synthetic-holdout.csv',rows))
            train_users,model=fitted[0]
            for row in rows:
                if row['user_id'] not in train_users:self.assertNotIn(row['profile_text'].split()[-1],model.vocabulary_)
            self.assertEqual(len(train_users),len(report['comparison']['train_users']))
    def test_semantic_metric_pending_preserves_separate_human_review(self):
        with tempfile.TemporaryDirectory() as root:
            rows=[dict(id='synthetic-answer',candidate='Prepare a resume.',reference='Prepare a resume.',human_factual_correct='true')]
            report=bertscore(self.file(root,'synthetic-answers.csv',rows))
            self.assertEqual(report['status'],'not_measured');self.assertIsNone(report['metrics']);self.assertEqual(report['human_review']['reviewed'],1)
    def test_warm_hybrid_selects_weight_on_prior_validation_only(self):
        with tempfile.TemporaryDirectory() as root:
            rows=[dict(user_id=f'synthetic-{u}',item_id=f'item-{(u+i)%10}',rating=1+(u+i)%5,profile_text='python development',item_text=f'python skill{(u+i)%10}',occurred_at=f'2026-10-{i+1:02d}T00:00:00+00:00') for u in range(6) for i in range(10)]
            report=warm_hybrid(self.file(root,'synthetic-temporal.csv',rows))
            self.assertEqual(report['status'],'measured_offline');self.assertEqual(report['train_count'],36);self.assertEqual(report['validation_count'],12);self.assertEqual(report['test_count'],12)
            self.assertIn(report['configuration']['selected_alpha'],[0,.25,.5,.75,1]);self.assertEqual(len(report['comparison']['holdout_hashes']),12)
            self.assertEqual(set(report['comparison']['model']),set(report['comparison']['profile_only']))
if __name__=='__main__':unittest.main()
