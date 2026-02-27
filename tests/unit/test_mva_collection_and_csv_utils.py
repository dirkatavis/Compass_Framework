import csv
import textwrap

import pytest

from compass_core.mva_collection import MvaCollection, MvaItem, MvaStatus
from compass_core import csv_utils


@pytest.mark.new_slice
def test_mva_item_transitions_and_properties():
    item = MvaItem(mva='12345678')
    assert item.is_pending
    item.mark_processing()
    assert item.is_processing
    item.mark_completed({'vin': 'VIN123', 'desc': 'Car'})
    assert item.is_completed
    assert item.result == {'vin': 'VIN123', 'desc': 'Car'}
    item.mark_failed('something')
    assert item.is_failed
    assert item.error == 'something'
    item.reset()
    assert item.is_pending and item.result is None and item.error is None


@pytest.mark.new_slice
def test_mva_collection_counts_and_progress():
    coll = MvaCollection.from_list(['11111111', '22222222', '33333333'])
    assert coll.total_count == 3
    assert coll.pending_count == 3
    # complete one, fail one
    coll[0].mark_completed({'vin': 'V1', 'desc': 'D1'})
    coll[1].mark_failed('err')
    assert coll.completed_count == 1
    assert coll.failed_count == 1
    assert coll.pending_count == 1
    assert coll.progress_percentage == pytest.approx((1+1)/3*100.0)


@pytest.mark.new_slice
def test_to_results_list_variants():
    coll = MvaCollection()
    coll.add('11111111')
    coll.add('22222222')
    coll.add('33333333')
    coll[0].mark_completed({'vin': 'V1', 'desc': 'D1'})
    coll[1].mark_failed('not found')
    results = coll.to_results_list()
    # first should have vin/desc
    assert any(r.get('vin') == 'V1' for r in results)
    # second should have error
    assert any(r.get('error') == 'not found' for r in results)
    # third pending should have N/A values
    assert any(r.get('vin') == 'N/A' for r in results)


@pytest.mark.new_slice
def test_read_mva_list_basic_and_normalize(tmp_path):
    f = tmp_path / 'mvas.csv'
    f.write_text(textwrap.dedent('''
        MVA
        50227203
        #comment
        abcdefgh12345678
        00001234
    ''').lstrip())
    out = csv_utils.read_mva_list(str(f))
    # expect 3 valid entries (header skipped, comment ignored)
    assert len(out) == 3
    # first normalized to leading 8 digits
    assert out[0] == '50227203'
    # third entry should prefer leading 8 digits from alphanumeric
    assert out[1] == 'abcdefgh'[:8]
    # leading zeros retained in numeric normalization
    assert out[2] == '00001234'


@pytest.mark.new_slice
def test_read_mva_list_no_normalize_returns_raw(tmp_path):
    f = tmp_path / 'mvas2.csv'
    f.write_text('50227203\n')
    out = csv_utils.read_mva_list(str(f), normalize=False)
    assert out == ['50227203']


@pytest.mark.new_slice
def test_read_mva_list_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        csv_utils.read_mva_list(str(tmp_path / 'no.csv'))


@pytest.mark.new_slice
def test_write_results_csv_mixed_schema_raises(tmp_path):
    out = tmp_path / 'out.csv'
    results = [
        {'mva': '1', 'vin': 'V'},
        {'mva': '2', 'status_update_result': 'success'}
    ]
    with pytest.raises(ValueError):
        csv_utils.write_results_csv(results, str(out))


@pytest.mark.new_slice
def test_write_results_csv_vehicle_and_closeout(tmp_path):
    out_v = tmp_path / 'v.csv'
    veh = [{'mva': '1', 'vin': 'V1', 'desc': 'D1', 'error': ''}]
    csv_utils.write_results_csv(veh, str(out_v))
    # read back header
    with open(out_v, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header[0].lower() == 'mva'

    out_c = tmp_path / 'c.csv'
    close = [{'mva': '1', 'status_update_result': 'success', 'error': ''}]
    csv_utils.write_results_csv(close, str(out_c))
    with open(out_c, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
    assert 'status_update_result' in [h.lower() for h in header]


@pytest.mark.new_slice
def test_read_workitem_list_required_columns_and_normalize(tmp_path):
    f = tmp_path / 'workitems.csv'
    f.write_text(textwrap.dedent('''
        MVA,DamageType,SubDamageType,CorrectionAction
        123,Glass,Windshield,Fix
        #comment,_,_,_
        ,,,
    ''').lstrip())
    out = csv_utils.read_workitem_list(str(f))
    assert len(out) == 1
    assert out[0]['mva'] == '00000123'


@pytest.mark.new_slice
def test_read_workitem_list_missing_columns_raises(tmp_path):
    f = tmp_path / 'badwork.csv'
    f.write_text('A,B,C\n1,2,3\n')
    with pytest.raises(ValueError):
        csv_utils.read_workitem_list(str(f))
