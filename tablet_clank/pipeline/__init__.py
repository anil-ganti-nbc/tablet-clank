import json
from ..models import RunResult, utcnow
from ..normalization import normalize_candidate
from ..validation import validate
from ..collectors.html_catalogue import HtmlCatalogueCollector
from ..qualification import QualificationProvenance, material_identity, prepare as prepare_qualification, finish as finish_qualification

def process(db, collector, fixture_mode=False, *, provenance: QualificationProvenance | str = QualificationProvenance.UNKNOWN,
            scope_key: str | None = None, material_inputs: dict | None = None):
    source = collector.source; result = RunResult(source.id); started = utcnow()
    db.conn.execute("INSERT OR IGNORE INTO sources(id,manufacturer,region,kind,url,state) VALUES (?,?,?,?,?,?)", (source.id,source.manufacturer,source.region,source.kind,source.url,source.state))
    db.conn.execute("UPDATE sources SET manufacturer=?, region=?, kind=?, url=?, state=? WHERE id=?", (source.manufacturer,source.region,source.kind,source.url,source.state,source.id))
    cur = db.conn.execute("INSERT INTO collector_runs(source_id,started_at,status) VALUES (?,?,?)", (source.id,started,"running")); result.run_id=cur.lastrowid
    scope_key = scope_key or source.id
    material_basis = {
        "target": "tablet-clank",
        "collector": collector.__class__.__module__ + "." + collector.__class__.__qualname__,
        "source_id": source.id, "manufacturer": source.manufacturer,
        "region": source.region, "kind": source.kind, "url": source.url,
        "qualification_policy": "tablet-qualification-v1",
    }
    if material_inputs:
        material_basis["execution_configuration"] = material_inputs
    qualification = prepare_qualification(
        db, run_id=result.run_id, scope_key=scope_key,
        material=material_identity(material_basis), provenance=provenance,
    )
    try:
        candidates = collector.collect(); result.raw_count=len(candidates)
        for candidate in candidates:
            ok, reason = validate(candidate)
            if not ok:
                result.rejected_count += 1; result.drops.append(reason)
                db.conn.execute("INSERT INTO rejected_candidates(run_id,url,title,reason,raw_values) VALUES (?,?,?,?,?)", (result.run_id,candidate.url,candidate.title,reason,json.dumps(candidate.raw_values)))
                continue
            result.validated_count += 1; product = normalize_candidate(candidate)
            row = db.conn.execute("SELECT * FROM products WHERE identity_key=?", (product.identity_key,)).fetchone()
            baseline = db.conn.execute("SELECT baseline_complete FROM source_state WHERE source_id=?", (source.id,)).fetchone()
            if row is None:
                db.conn.execute("INSERT INTO products(manufacturer,family,name,model_number,sku,region,variant,connectivity,ram_gb,storage_gb,colour,processor,display_size_in,os,identity_key,first_seen,last_seen) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (product.manufacturer,product.family,product.name,product.model_number,product.sku,product.region,product.variant,product.connectivity,product.ram_gb,product.storage_gb,product.colour,product.processor,product.display_size_in,product.os,product.identity_key,product.observed_at,product.observed_at))
                pid=db.conn.execute("SELECT id FROM products WHERE identity_key=?", (product.identity_key,)).fetchone()[0]
                result.new_count += 1
                event_type = "new_product"
                if source.id in ("apple_us_ipad_pro_store", "apple_in_ipad_pro_store") and product.sku:
                    repaired = db.conn.execute("SELECT 1 FROM products WHERE id<>? AND manufacturer=? AND region=? AND sku=? LIMIT 1", (pid, product.manufacturer, product.region, product.sku)).fetchone()
                    if repaired:
                        event_type = "identity_correction"
                if baseline and baseline[0]: db.conn.execute("INSERT INTO change_events(product_id,source_id,event_type,new_value,evidence_url,observed_at,confidence,run_id) VALUES (?,?,?,?,?,?,?,?)", (pid,source.id,event_type,product.name,product.url,product.observed_at,.85,result.run_id))
            else:
                pid=row["id"]; result.resighted_count += 1
                changed=[]
                for field in ("processor","ram_gb","storage_gb","connectivity","display_size_in","os"):
                    if row[field] != getattr(product,field) and getattr(product,field) is not None: changed.append((field,row[field],getattr(product,field)))
                for field, old, new in changed:
                    result.updated_count += 1
                    if baseline and baseline[0]: db.conn.execute("INSERT INTO change_events(product_id,source_id,event_type,old_value,new_value,evidence_url,observed_at,confidence,run_id) VALUES (?,?,?,?,?,?,?,?,?)", (pid,source.id,"spec_change",str(old),str(new),product.url,product.observed_at,.8,result.run_id))
                db.conn.execute("UPDATE products SET last_seen=?, name=? WHERE id=?", (product.observed_at, product.name, pid))
            db.conn.execute("INSERT OR IGNORE INTO observations(product_id,source_id,url,observed_at,raw_values,normalized_values,collector) VALUES (?,?,?,?,?,?,?)", (pid,source.id,product.url,product.observed_at,json.dumps(product.raw_values),json.dumps(product.__dict__),collector.__class__.__name__))
            result.accepted_count += 1
        if result.accepted_count == 0: raise RuntimeError("zero accepted candidates; source is not healthy")
        state=db.conn.execute("SELECT baseline_complete FROM source_state WHERE source_id=?",(source.id,)).fetchone()
        if not state: db.conn.execute("INSERT INTO source_state(source_id,baseline_complete,last_healthy_run_id,consecutive_healthy_runs) VALUES (?,?,?,?)",(source.id,1,result.run_id,1))
        else: db.conn.execute("UPDATE source_state SET baseline_complete=1,last_healthy_run_id=?,consecutive_healthy_runs=consecutive_healthy_runs+1 WHERE source_id=?",(result.run_id,source.id))
        result.status="success"
    except Exception as exc:
        result.status="failed"; result.error=str(exc)
        # Health honesty (Fleet Law 3): the healthy-streak counter must not
        # survive a failed run — a monotonic counter would keep reporting
        # pre-outage health forever. Zero accepted candidates and transport
        # failures both land here.
        db.conn.execute("UPDATE source_state SET consecutive_healthy_runs=0 WHERE source_id=?", (source.id,))
    db.conn.execute("UPDATE collector_runs SET finished_at=?,status=?,raw_count=?,validated_count=?,rejected_count=?,accepted_count=?,new_count=?,updated_count=?,resighted_count=?,error=? WHERE id=?", (utcnow(),result.status,result.raw_count,result.validated_count,result.rejected_count,result.accepted_count,result.new_count,result.updated_count,result.resighted_count,result.error,result.run_id)); db.conn.commit()
    finish_qualification(db, qualification, result.status)
    return result
