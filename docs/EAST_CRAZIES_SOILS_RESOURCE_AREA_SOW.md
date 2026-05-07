# East Crazies EA Soils Specialist Report Scope Of Work

Date: 2026-05-07

This scope of work defines the soils-resource fieldwork, analysis, documentation, and
deliverables needed to prepare a Soils Specialist Report for the East Crazy Inspiration Divide
Land Exchange Environmental Assessment on the Custer Gallatin National Forest. It is written so a
consultant, Forest Service soils specialist, or interdisciplinary resource specialist can understand
the work needed to complete the soils report and provide report-ready input to the EA.

This SOW is a Project SOW planning and contracting support artifact. It is not a final SOW award
document, an applicability decision, a compliance finding, legal advice, a legal sufficiency
determination, or a final agency decision.

## Research Basis

Use this SOW with the current Project SOW package docs and these external authorities, guidance
documents, and example soil-analysis artifacts:

- Forest Service NEPA procedures at 36 CFR 220.4 and 36 CFR 220.7. An EA must support planning,
  decision-making, and public disclosure; include need, proposed action and alternatives, effects,
  and agencies/persons consulted; and provide enough evidence and analysis to support an EIS or
  FONSI determination.
- Custer Gallatin Land Management Plan, January 2022. The plan is the comprehensive forest-level
  direction for management, use, and protection of the Custer Gallatin National Forest. The soils
  monitoring table identifies FW-DC-SOIL-01, FW-STD-SOIL-01, and MON-SOIL-01, with detrimental
  soil disturbance (DSD) measured as pre- and post-implementation percent DSD of the monitored
  activity area. The same monitoring table identifies FW-DC-SOIL-02, FW-GDL-SOIL-07, and
  MON-SOIL-02 for coarse woody debris in forested vegetation management units.
- Forest Service Soil Quality Monitoring resources, including Forest Soil Disturbance Monitoring
  Protocol Volumes I and II and the Soil-Disturbance Field Guide. These provide the expected
  terminology and visual-disturbance framework for soil-disturbance classes, field consistency, and
  pre/post-treatment monitoring.
- NRCS Web Soil Survey and SSURGO soils data. Web Soil Survey is the official National Cooperative
  Soil Survey source for soil map units, reports, tabular data, thematic maps, and GIS downloads.
- Forest Service National Best Management Practices Program. National Core BMPs are broad,
  non-prescriptive "what to do" practices; site-specific design must also use state, tribal, local,
  regional, and land-management-plan direction.
- Published Forest Service soils-resource analyses such as the Waterman West Soil Specialist Report
  and Mower Tract EA soils section. These examples show the expected report components: regulatory
  framework, methods, affected environment, existing condition, direct/indirect/cumulative effects,
  mitigation/design features, Forest Plan consistency, and appendices with maps, activity units,
  and soil map unit crosswalks.

## Project And Package Basis

Source artifacts reviewed for this East Crazies SOW:

- `docs/PROJECT_SOW_PACKAGE_RUNBOOK.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/PROJECT_SOW_OPERATIONALIZATION_ACCEPTANCE_MATRIX.md`
- `config/project_sow_resource_scopes_v1.json`
- `config/fixtures/project_sow/east_crazies_land_exchange_intake.json`
- Generated East Crazies Project SOW package smoke output under
  `/tmp/east-crazies-soils-sow-package/`

Current package facts:

- Project: East Crazy Inspiration Divide Land Exchange Proposed Action
- Forest: Custer Gallatin National Forest
- District: Bozeman Ranger District
- NEPA level: environmental assessment
- Project type: land exchange
- Forest plan profile: `custer_gallatin`
- Resource area: `soil_resources`
- Selected resource scope: `vegetation_soils_air_quality`
- Resource-scope discipline: `vegetation_soils_air`
- Soil-resource package status: covered by a selected SOW scope
- Current intake status: `soil_resources` is not explicitly listed as an expected
  proposed-action-derived resource area
- Observed East Crazies calibration package status: no standalone soils specialist report is listed
  in `observed_specialist_reports[]`

Important boundary: the current intake covers soils through the combined vegetation, soils, air
quality, climate, and carbon scope. That is sufficient to trigger a soils SOW, but it is not
sufficient to decide whether a standalone Soils Specialist Report is unnecessary. This SOW requires
the soils specialist to document that decision with evidence.

## Objective

Prepare a complete Soils Specialist Report, or a documented no-issue/incorporated-analysis memo if
the responsible Forest Service soils reviewer determines a standalone report is not warranted. The
work product must be complete enough for the EA team to disclose soil-resource effects, evaluate
Forest Plan consistency, support project design criteria and mitigation, and place a defensible
soils analysis in the administrative record.

The report must identify and analyze whether the proposed land exchange, trail and trailhead work,
road and trail access commitments, grazing-related improvements, wetland and riparian protections,
parcel conveyance/acquisition, and post-exchange management assumptions could affect:

- detrimental soil disturbance;
- soil productivity and long-term site productivity;
- compaction, rutting, puddling, displacement, and loss of soil structure;
- erosion, mass movement, slope stability, sediment delivery, and drainage alteration;
- soil organic matter, litter/duff, coarse woody debris, and revegetation capacity;
- wet or hydric soils, riparian soils, and soils connected to aquatic or wetland resources;
- invasive-plant establishment risk and restoration success;
- climate and carbon analysis assumptions that depend on soil condition or soil carbon;
- implementation feasibility and mitigation effectiveness.

## Required Consultant Qualifications

The contractor or assigned specialist must provide personnel with documented experience in forest
soil-resource analysis for NEPA or comparable land-management projects. At least one lead analyst
must meet one of these qualifications:

- soil scientist, hydrologist, watershed specialist, or natural resource specialist with direct
  professional experience in soil-disturbance, erosion, and soil-productivity analysis on National
  Forest System lands;
- consultant with demonstrated Forest Service NEPA specialist-report experience and access to a
  qualified soils reviewer;
- Custer Gallatin or Region 1 soils/watershed specialist assigned by the Forest Service.

The field lead must be trained or demonstrably competent in applying Forest Service
soil-disturbance class concepts, recording field observations, collecting GPS/photo evidence, and
coordinating soils issues with hydrology, wetlands, roads/trails, vegetation, botany, range, realty,
minerals, and hazardous-materials specialists.

## Government-Furnished Information

The Forest Service project lead or contracting officer's representative should provide the following
before fieldwork begins:

- current proposed action, purpose and need, and any alternatives or design changes under review;
- GIS parcel boundaries for federal disposal parcels and non-federal acquisition parcels;
- proposed trail, trail relocation, road, trailhead, access-easement, construction, closure,
  decommissioning, and improvement footprints;
- wetland, riparian, stream, lake, floodplain, and aquatic-resource layers;
- grazing allotment, fence, road, irrigation ditch, range-improvement, and special-use layers;
- existing roads, trails, unauthorized routes, travel management data, and road/trail maintenance
  status;
- Custer Gallatin Land Management Plan direction, relevant plan-component crosswalks, and any
  forest- or district-level soil-quality direction;
- available recent aerial imagery, LiDAR, slope, geology, landslide, erosion-hazard, burn-history,
  vegetation, invasive-species, and hydrology layers;
- prior East Crazies specialist reports, EA sections, maps, design criteria, mitigation commitments,
  and public comments related to soils, roads, trails, wetlands, hydrology, grazing, vegetation, or
  restoration;
- land exchange case file constraints that affect access, title, reserved rights, implementation
  conditions, or parcel management assumptions;
- format requirements for report, maps, GIS, photo logs, and administrative-record files.

If any required information is unavailable, the specialist must list it in the work plan and explain
how the analysis will proceed without it or why the absence is a stop condition.

## Action Elements To Analyze

Analyze soils effects for each applicable action element. At minimum, the report must address:

1. Land exchange parcels.
   - Federal parcels leaving National Forest System ownership.
   - Non-federal parcels entering National Forest System ownership.
   - Any management change that could alter erosion risk, restoration needs, road/trail use,
     grazing pressure, vegetation condition, or watershed function.

2. Trails, roads, access, and trailhead work.
   - Sweet Trunk Trail No. 274 construction.
   - Inspiration Divide Trail No. 8 relocation.
   - Big Timber Canyon Trailhead improvement.
   - Road and trail easements, reserved access, and any road/trail closure, relocation,
     decommissioning, conversion, or reconstruction.

3. Wetland, riparian, and aquatic-resource protections.
   - Deed restrictions, retained wetlands, monitoring access, stream/riparian buffers, and
     restoration commitments.
   - Soil-water connectivity, sediment delivery, hydric or wet soils, and access or construction
     effects near wetlands and riparian management zones.

4. Grazing and range improvements.
   - Affected allotments, term permits, fences, roads, irrigation ditches, water developments, and
     related range improvements.
   - Soil compaction, bare ground, bank disturbance, erosion, and restoration needs where grazing
     use or infrastructure changes.

5. Hazardous materials, minerals, and realty due diligence.
   - Site-condition constraints, mine waste, recognized environmental conditions, mineral
     reservations, and closing conditions that could affect soil handling, avoidance, disclosure, or
     mitigation.

6. Vegetation, restoration, invasive species, climate, and carbon.
   - Soil assumptions supporting revegetation, weed prevention, restoration, carbon storage,
     vegetation cover, whitebark pine or botany work, and climate/carbon discussion.

## Fieldwork Plan

The contractor must submit a fieldwork plan for Forest Service review before mobilizing. The plan
must include:

- field objectives and decision questions;
- project area and soil-analysis area maps;
- proposed activity-area units;
- proposed field transects, observation points, photo points, and verification areas;
- data forms and GPS/photo naming conventions;
- planned soil-disturbance class method;
- safety plan, access assumptions, communications plan, and landowner or road/trail access needs;
- weather, snow, and soil-moisture constraints;
- schedule and field crew roles.

Fieldwork must occur during a snow-free period when soil surface conditions, drainage, erosion
features, compaction/rutting, litter/duff, vegetation cover, and wet or hydric indicators can be
observed. If wet-season or post-storm verification is needed to evaluate runoff, drainage, or
erosion features, the specialist must identify that need and propose a targeted revisit.

## Field Methods

The field effort must be sufficient to verify map assumptions and support quantified effects
analysis. Use a combination of office GIS, soil survey data, professional judgment, and field
verification. The report must describe the selected method and why it is appropriate.

Required field methods:

- Delineate activity areas by proposed action component, such as trail construction, trail
  relocation, trailhead improvement, access route, road closure, wetland/riparian protection area,
  grazing improvement, restoration area, or parcel management unit.
- Use the Forest Service soil-disturbance class framework to record existing soil disturbance and
  estimate post-implementation disturbance where activity footprints are proposed.
- Verify NRCS soil map units, slope classes, landforms, drainage, hydric/wet indicators, erosion
  features, and sensitive soil conditions where proposed activities intersect them.
- Record existing compaction, rutting, displacement, puddling, bare soil, erosion, gullies,
  mass-movement features, sediment-routing pathways, road/trail drainage, stream/wetland
  connectivity, and soil-cover conditions.
- Record litter/duff, coarse woody debris, ground cover, rock fragments, vegetation cover,
  invasive-species indicators, and restoration/revegetation constraints where they affect soil
  productivity or erosion.
- Collect GPS points, representative photos, and field notes for each activity-area unit and each
  sensitive feature that materially affects the analysis.
- Use soil pits, shovel checks, probe observations, or comparable field checks as needed to verify
  depth, texture, restrictive layers, wetness, compaction, or restoration feasibility. Laboratory
  analysis is not required unless the Forest Service soils reviewer identifies a specific question
  that cannot be resolved by field observation and existing data.
- Coordinate in the field or during post-field review with hydrology/wetlands, roads/trails,
  vegetation/botany, range, realty, minerals, and hazardous-materials reviewers where soil effects
  overlap their resource areas.

Minimum field record:

- activity-area ID;
- date, observer, weather, and soil-moisture condition;
- location method and GPS/photo IDs;
- soil map unit and field-verified soil/landform notes;
- slope class and landform;
- existing disturbance class and disturbance type;
- expected disturbance source and estimated acreage or length;
- erosion, sediment-delivery, and drainage observations;
- wetland/riparian or hydric-soil indicator notes where present;
- mitigation/BMP need;
- uncertainty or revisit need.

## Analysis Area And Timeframes

The report must define spatial and temporal bounds for the soils analysis.

Spatial bounds:

- Direct effects: activity areas where ground disturbance, access, construction, relocation,
  decommissioning, restoration, grazing-infrastructure change, or soil handling is proposed.
- Indirect effects: connected slopes, drainage paths, wetlands/riparian areas, road/trail drainage
  networks, and sediment-routing areas where soil effects could move beyond the activity footprint.
- Cumulative effects: project boundary plus any watershed, travel-route, allotment, or parcel
  context needed to evaluate additive soil disturbance and sediment effects from past, present, and
  reasonably foreseeable future actions.

Temporal bounds:

- Existing condition: current field-observed and GIS/record condition at the time of analysis.
- Short term: implementation through approximately 10 years, or the period until disturbed soils
  are expected to stabilize and revegetate.
- Long term: the period in which soil productivity, drainage, erosion, compaction, and ownership or
  management changes could continue to affect soil function. Explain if a different timeframe is
  more appropriate for a specific effect.

## Analysis Requirements

The Soils Specialist Report must provide the following analyses.

### Regulatory And Management Framework

Summarize the soil-resource requirements and analysis criteria used for the report, including:

- NEPA EA content requirements and effects-disclosure needs;
- NFMA and Custer Gallatin Land Management Plan consistency;
- applicable Forest Plan soil desired conditions, standards, guidelines, monitoring indicators, and
  relevant watershed/roads/trails/riparian plan components;
- Forest Service soil-disturbance class and soil-quality monitoring guidance;
- NRCS soil survey source data and limitations;
- National Core BMPs, Montana/state water-quality or erosion-control requirements, and any
  Custer Gallatin or Region 1 soil/water BMP direction supplied by the Forest Service.

### Affected Environment And Existing Condition

Describe current soil-resource conditions in enough detail to support effects analysis:

- soil map units, landforms, slope classes, parent material, drainage, hydrologic groups, erosion
  hazard, rutting/compaction limitations, revegetation limitations, and sensitive soil attributes;
- existing roads, trails, trailheads, grazing improvements, unauthorized routes, wetland/riparian
  conditions, and disturbed areas;
- existing detrimental soil disturbance by activity area where field-observed or reasonably
  estimable;
- soil conditions on federal parcels leaving ownership and non-federal parcels entering ownership,
  with any limitations on access or data certainty;
- current soil-water connectivity, sediment-routing pathways, and locations where soil disturbance
  could affect wetlands, streams, riparian areas, aquatic habitat, or water quality;
- current restoration, revegetation, weed, carbon, or productivity constraints.

### Effects Analysis

Analyze the proposed action, no-action baseline, and any other alternatives supplied by the Forest
Service. The effects analysis must:

- quantify expected soil disturbance by activity area, action element, alternative, and soil map
  unit when the data allow;
- estimate DSD acres and percent of each relevant activity area before and after implementation;
- identify where proposed disturbance may approach or exceed applicable Custer Gallatin or
  Region 1 soil-quality thresholds;
- evaluate direct, indirect, and cumulative effects to soil productivity, compaction, rutting,
  puddling, displacement, erosion, sediment delivery, slope stability, mass movement, hydrologic
  function, soil organic matter, litter/duff, coarse woody debris, and revegetation capacity;
- evaluate permanent versus temporary disturbance and disclose how long recovery is expected to
  take;
- evaluate whether acquired parcels improve, maintain, or create soil-management needs on National
  Forest System lands;
- evaluate whether federal disposal parcels include soil-resource constraints that require deed,
  reserved-right, monitoring-access, or implementation conditions;
- identify soil effects that cannot be fully avoided, soil effects reduced by mitigation, and soil
  effects that remain uncertain;
- disclose assumptions and data gaps clearly enough for the responsible official and public to
  understand the limits of the analysis.

### Cumulative Effects

Evaluate cumulative soil effects using spatial and temporal bounds appropriate to the project.
Consider past, present, and reasonably foreseeable future actions only when they have a useful and
relevant cause-and-effect relationship with the soils effects of the proposed action. At minimum,
screen:

- existing roads, trails, trailheads, and unauthorized routes;
- grazing use and range improvements;
- past or planned trail construction, road work, restoration, or decommissioning;
- wetland/riparian restoration or disturbance;
- private-land actions that may affect connected slopes, drainages, roads, or wetlands where data
  are reasonably available;
- vegetation, fuels, invasive-species, or restoration projects that alter soil cover, erosion, or
  recovery assumptions.

### Mitigation, Design Criteria, BMPs, And Monitoring

Prepare a mitigation and BMP matrix. Each row must include the action element, soil concern,
location or activity-area trigger, design criterion/BMP/mitigation, responsible party, timing, and
verification method.

At minimum, address:

- erosion and sediment control for trail, road, trailhead, and construction work;
- drainage spacing, waterbars, grade reversals, rolling dips, cross-drains, armoring, and outsloping
  where roads or trails could concentrate runoff;
- wet-weather restrictions and seasonal operating limits;
- equipment exclusion or low-impact methods for wet soils, steep slopes, high erosion hazard,
  mass-movement risk, riparian areas, and sensitive soil map units;
- topsoil/duff salvage and replacement where soil handling occurs;
- decompaction, ripping, scarification, recontouring, and site preparation where needed;
- weed-free seed, mulch, erosion-control materials, native revegetation, and post-disturbance cover
  targets;
- protection of coarse woody debris and soil organic matter where forested vegetation units are
  affected;
- avoidance buffers for wetlands, streams, seeps, springs, unstable slopes, or hydric soils;
- monitoring requirements, including pre- and post-implementation DSD monitoring where vegetation
  or ground-disturbing activity areas trigger the Forest Plan monitoring question.

## Required Report Structure

The Soils Specialist Report must include these sections:

1. Executive summary.
   - Bottom-line findings.
   - Whether a standalone soils report is required or, if this is the report, whether the analysis
     supports the EA record.
   - Key mitigation, monitoring, and unresolved issues.

2. Project description and alternatives.
   - Proposed action elements relevant to soils.
   - No-action baseline and any action alternatives analyzed.
   - Activity-area definitions.

3. Regulatory and management framework.
   - NEPA, NFMA, Custer Gallatin Land Management Plan, soil-quality monitoring, NRCS data, and BMP
     framework.

4. Methods.
   - GIS and desktop review.
   - Soil survey and field verification methods.
   - Soil-disturbance class method.
   - Analysis indicators and thresholds.
   - Cumulative effects bounds.
   - Assumptions, limitations, and data gaps.

5. Affected environment.
   - Existing soil, landform, slope, disturbance, hydrology, road/trail, wetland/riparian,
     vegetation, grazing, and restoration conditions.

6. Environmental consequences.
   - Direct, indirect, and cumulative effects by alternative and action element.
   - Quantified disturbance tables and DSD analysis.
   - Soil productivity, erosion/sediment, compaction, displacement, wet soils, slope stability,
     restoration, invasive species, and carbon/vegetation interactions.

7. Forest Plan consistency.
   - Custer Gallatin soils plan components.
   - Relevant watershed, roads/trails, riparian, vegetation, and grazing components.
   - Consistency finding or unresolved consistency questions for the responsible official.

8. Mitigation, BMPs, design criteria, and monitoring.
   - Required implementation measures.
   - Monitoring requirements and success criteria.
   - Responsible parties and timing.

9. Unavoidable adverse effects, irreversible or irretrievable commitments, and short-term versus
   long-term productivity considerations, as applicable to the soils resource.

10. References and administrative-record index.
    - Sources cited.
    - Data layers, field forms, photos, maps, and communications used.

11. Appendices.
    - Soil map unit tables.
    - Activity-area by soil map unit crosswalk.
    - DSD calculations.
    - Field forms.
    - Photo log.
    - GIS layer list.
    - Map atlas.
    - QA/QC checklist.

## Required Tables And Figures

The final report must include or append these tables and figures:

- project location and soil-analysis area map;
- proposed-action activity-area map;
- soil map unit map and table;
- slope and erosion-hazard map;
- hydrology/wetland/riparian connectivity map;
- road/trail/trailhead and grazing-improvement disturbance map;
- field observation and photo point map;
- activity-area by soil map unit crosswalk;
- existing and expected DSD table by activity area;
- proposed disturbance and recovery table by action element;
- mitigation/BMP/monitoring matrix;
- Forest Plan consistency matrix;
- data-gap and uncertainty table.

Maps must include scale, north arrow, coordinate system, data date, project boundary, activity-area
IDs, and source attribution. GIS deliverables must use agreed projection and naming conventions and
must be usable by the Custer Gallatin GIS/ID team without rework.

## Deliverables

Deliverables are required unless the contracting officer's representative waives them in writing.

1. Kickoff notes and information-request log.
   - Due after kickoff meeting.
   - Must identify missing government-furnished information and stop conditions.

2. Fieldwork plan.
   - Due before mobilization.
   - Must include field methods, maps, safety/access plan, field forms, sampling/observation plan,
     schedule, and coordination needs.

3. Field data package.
   - GIS points, tracks, and activity-area refinements.
   - Completed field forms.
   - Geotagged photo log.
   - Field notes.
   - Initial field findings memo with urgent design or mitigation issues.

4. Draft Soils Specialist Report.
   - Report text, tables, maps, appendices, and administrative-record index.
   - Must be complete enough for ID team review and EA incorporation.

5. Draft EA soils section.
   - Concise affected-environment and environmental-consequences text suitable for the EA.
   - Must cross-reference the specialist report rather than duplicating all technical detail.

6. Forest Plan consistency and mitigation package.
   - Plan consistency matrix.
   - Mitigation/BMP/monitoring matrix.
   - DSD calculation workbook or table.

7. Final Soils Specialist Report.
   - Clean final report.
   - Comment-response or change log.
   - Final maps, tables, appendices, and administrative-record index.

8. Final data package.
   - GIS layers.
   - PDF map atlas.
   - Photo log.
   - Field forms.
   - Source data inventory.
   - Data limitations memo.

Preferred formats:

- report: `.docx` or editable text plus PDF;
- EA section: editable text;
- tables: `.xlsx` or `.csv`;
- GIS: file geodatabase or geopackage plus shapefile exports if requested;
- photos: `.jpg` with photo log;
- maps: PDF plus source GIS project or layout files if requested.

## Acceptance Criteria

The Forest Service may reject deliverables that do not satisfy these criteria:

- The report answers whether soils require a standalone specialist report, incorporated analysis,
  or no-issue memo, and explains the evidence basis for that decision.
- The analysis uses the project-specific action elements, activity areas, and Custer Gallatin
  Forest Plan context.
- Fieldwork is documented well enough to trace observations to locations, photos, and activity
  areas.
- Every soil concern is tied to a proposed-action element, parcel, or implementation footprint.
- DSD, soil productivity, erosion, compaction, displacement, rutting, slope stability, sediment
  delivery, organic matter, coarse woody debris, restoration, and invasive-species prevention are
  analyzed or explicitly screened out.
- Direct, indirect, and cumulative effects are disclosed with clear spatial and temporal bounds.
- Mitigation, BMP, restoration, and monitoring commitments are listed as requirements, not assumed
  conclusions.
- Soil assumptions that support hydrology, wetlands, roads/trails, vegetation, carbon, grazing,
  realty, minerals, or hazardous-materials work are visible and coordinated.
- Forest Plan consistency is explicitly evaluated.
- The administrative record can trace every material claim to field data, GIS data, soil survey
  data, specialist judgment, or cited source material.
- Final PDF starts with a valid `%PDF-` header and the editable source is preserved.

## Schedule And Review Points

Use this default schedule unless the Forest Service provides a project-specific schedule:

- Week 1: kickoff, data transfer, information-request log.
- Week 2: desktop review, GIS activity-area setup, draft fieldwork plan.
- Weeks 3-5: fieldwork during suitable soil-observation conditions.
- Week 6: field findings memo and refined analysis plan.
- Weeks 7-9: draft Soils Specialist Report, map atlas, mitigation matrix, and EA soils section.
- Weeks 10-11: Forest Service/ID team review and comment resolution.
- Week 12: final report and final data package.

Stop conditions:

- Project footprint or action elements are too incomplete to define activity areas.
- Access to key activity areas or parcels is not available.
- Snow, frozen ground, wildfire closure, unsafe access, or saturated conditions prevent reliable
  field verification.
- Forest Service plan-component direction or DSD threshold direction is unresolved.
- Missing GIS or parcel data prevents meaningful effects quantification.

## Reviewer Role And Timing

Reviewer role: Custer Gallatin soils specialist, watershed specialist, or designated Forest Service
interdisciplinary reviewer with soils expertise.

Review timing:

- approve fieldwork plan before mobilization;
- review initial field findings before draft report production;
- review draft report and mitigation matrix before draft EA effects text is finalized;
- sign off on final report before decision-record mitigation, design criteria, or implementation
  commitments rely on soils assumptions.

Recommended signoff fields:

- `soils_analysis_boundary_confirmed`
- `activity_areas_confirmed`
- `soil_data_sources_confirmed`
- `field_review_complete`
- `field_review_limitations_disclosed`
- `dsd_analysis_confirmed`
- `soil_effects_pathway_confirmed`
- `forest_plan_consistency_confirmed`
- `bmp_mitigation_monitoring_confirmed`
- `standalone_soils_report_need_confirmed`

## Open Forest Service Decisions

The Forest Service must resolve these before final report acceptance:

- Should the East Crazies intake be amended to list `soil_resources` as an explicit
  proposed-action-derived resource area?
- Which Forest Service soil-quality threshold, Region 1 direction, and Custer Gallatin plan
  components must be applied to this project?
- Is a standalone Soils Specialist Report required, or can soils be documented through an
  incorporated-analysis/no-issue memo?
- Which action alternatives, if any, must be analyzed beyond proposed action and no action?
- Is field verification required on both federal disposal and non-federal acquisition parcels?
- Which soil BMPs, design criteria, monitoring requirements, and implementation commitments must
  be carried into the EA, decision record, and implementation file?
- Which GIS/data package format is required by the Custer Gallatin ID team?

## Source Links

- 36 CFR 220.4, Forest Service NEPA general requirements:
  https://ecfr.io/Title-36/Section-220.4
- 36 CFR 220.7, Environmental assessment and decision notice:
  https://ecfr.io/Title-36/Section-220.7
- Custer Gallatin Land Management Plan page:
  https://www.fs.usda.gov/r01/custergallatin/planning/forest-plan/custer-gallatin-land-management-plan-forest-plan-revision
- Custer Gallatin Land Management Plan PDF:
  https://www.fs.usda.gov/media/51590
- Forest Service Soil Quality Monitoring resources:
  https://www.fs.usda.gov/soils/monitoring.shtml
- Forest Service Soil-Disturbance Field Guide:
  https://www.fs.usda.gov/t-d/php/library_card.php?p_num=0819+1815P
- NRCS Web Soil Survey:
  https://www.nrcs.usda.gov/resources/data-and-reports/web-soil-survey
- Forest Service National Best Management Practices Program:
  https://www.fs.usda.gov/naturalresources/watershed/bmp.shtml
- Waterman West Soil Specialist Report example:
  https://www.govinfo.gov/content/pkg/GOVPUB-A13-PURL-gpo111718/pdf/GOVPUB-A13-PURL-gpo111718.pdf
- Mower Tract EA soils analysis example:
  https://www.fs.usda.gov/emc/nepa/revisions/includes/docs/restoration/proposedces/mowertract-ea.pdf
