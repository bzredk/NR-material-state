from real_data_intake import validate_rows


def sample():
    rows=[dict(episode_id='A',specimen_id='pad1',session_id='day1',timestamp=str(i*2),
      command_position='5',actual_position=str(i),normal_force='2') for i in range(4)]
    meta=dict(data_type='synthetic_validation',units=dict(time='ms',position='mm',force='N'))
    return rows,meta


def test_units_and_time_conversion():
    rows,meta=sample();normalized,report=validate_rows(rows,meta)
    assert report['status']=='passed'
    assert normalized[-1]['timestamp_s']==.006 and normalized[-1]['actual_position_m']==.003
    assert report['episodes'][0]['sampling_rate_Hz']==500.


def test_bad_time_and_nonfinite_rejected():
    rows,meta=sample();rows[2]['timestamp']=rows[1]['timestamp']
    assert validate_rows(rows,meta)[1]['status']=='failed'
    rows,meta=sample();rows[1]['normal_force']='nan'
    assert validate_rows(rows,meta)[1]['status']=='failed'


def test_ambiguous_units_rejected():
    rows,meta=sample();meta['units']['position']='unknown'
    assert validate_rows(rows,meta)[1]['status']=='failed'
