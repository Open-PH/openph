# OpenPH Implementation Plan

**Status**: 🚧 In Progress  
**Last Updated**: October 14, 2025  
**Current Phase**: Phase 0 - Repository Setup

---

## Overview

This plan guides the migration from the monolithic `ph-energy` repository to the modular OpenPH ecosystem. We will build the new repositories incrementally, leaving the current `ph-energy` repository unchanged until all new repositories are functional.

## Repository Organization

### GitHub Organization
- **Name**: `Open-PH`
- **URL**: `https://github.com/Open-PH`
- **Status**: ✅ Organization created

### New Repositories
1. **openph** - Core engine and plugin architecture
2. **openph-ground** - Ground coupling calculations  
3. **openph-solar** - Solar radiation calculations
4. **openph-energy-demand** - Energy demand calculations (heating/cooling/DHW)

### Directory Structure Pattern ⚠️ IMPORTANT

**Workspace Container**: `openph-workspace/`
- This is NOT a git repository
- Contains shared `.venv/` and all package repositories
- Location: `~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace/`

**Package Structure Pattern**: `<workspace>/<package>/src/<modules>`

Each package follows this **flat src/ structure**:
```
openph-workspace/                    # ← Workspace container (NOT a git repo)
├── .venv/                           # ← Shared Python 3.10.18 virtual environment
├── openph/                          # ← Package repository (IS a git repo)
│   ├── .git/
│   ├── pyproject.toml
│   ├── src/                         # ← Source directory
│   │   ├── __init__.py              # ← Package root (openph package)
│   │   ├── attributes/              # ← Module directories
│   │   ├── model/
│   │   └── solvers/
│   └── tests/
├── openph-ground/                   # ← Separate git repo
│   ├── .git/
│   ├── pyproject.toml
│   ├── src/                         # ← Flat structure (NO nested openph_ground/)
│   │   ├── __init__.py              # ← Package root (openph_ground package)
│   │   ├── ground_solver.py         # ← Module files directly in src/
│   │   └── calc_periods.py
│   └── tests/
├── openph-solar/                    # ← Separate git repo
│   └── src/                         # ← Same flat pattern
│       ├── __init__.py              # ← Package root (openph_solar package)
│       └── solar_solver.py
└── openph-energy-demand/            # ← Separate git repo
    └── src/                         # ← Same flat pattern
        ├── __init__.py              # ← Package root (openph_energy_demand package)
        ├── heating_demand.py
        ├── cooling_demand.py
        └── calc_periods/
```

**Key Points**:
- ❌ **WRONG**: `src/openph_ground/ground_solver.py` (extra nesting)
- ✅ **CORRECT**: `src/ground_solver.py` (flat structure)
- Each `src/` contains package modules **directly**, not in a nested package folder
- Configure with explicit `packages` list and `package-dir` mapping in `pyproject.toml`
- All repos share the same `.venv` at workspace level

**pyproject.toml Pattern**:
```toml
[tool.setuptools]
packages = ["openph_ground", "openph_ground.calc_periods"]  # Explicit list
package-dir = {"openph_ground" = "src"}  # Maps package to src directory
```

---

## Phase 0: Repository Setup ✅ COMPLETE

**Goal**: Create GitHub repositories and basic structure for all OpenPH packages.

### Step 0.1: Create Core Repository - `openph`
- [x] Create repository `Open-PH/openph` on GitHub
  - Description: "Open source Passive House calculation engine with extensible plugin architecture"
  - Public repository
  - Initialize with README
  - Add MIT license
- [x] Clone repository locally
- [x] Create basic directory structure (flat src/ pattern):
  ```
  openph-workspace/openph/           # Inside workspace container
  ├── README.md
  ├── LICENSE
  ├── pyproject.toml
  ├── src/                           # Flat structure - NO nested openph/ folder
  │   ├── __init__.py                # Package root
  │   ├── attributes/
  │   ├── model/
  │   └── solvers/
  └── tests/
      └── __init__.py
  ```
  **Note**: `src/` contains package modules directly (NOT `src/openph/`)

### Step 0.2: Create Solver Repositories
- [x] Create repository `Open-PH/openph-ground`
  - Description: "Ground coupling and foundation heat transfer calculations for OpenPH"
  - Public, README, MIT license
- [x] Create repository `Open-PH/openph-solar`
  - Description: "Solar radiation calculations for OpenPH"
  - Public, README, MIT license
- [x] Create repository `Open-PH/openph-energy-demand`
  - Description: "Energy demand calculations (heating, cooling, DHW) for OpenPH"
  - Public, README, MIT license

### Step 0.3: Setup Local Development Environment
- [x] Create parent directory structure:
  ```bash
  mkdir -p ~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace
  cd ~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace
  ```
- [x] Clone all repositories:
  ```bash
  git clone https://github.com/Open-PH/openph.git
  git clone https://github.com/Open-PH/openph-ground.git
  git clone https://github.com/Open-PH/openph-solar.git
  git clone https://github.com/Open-PH/openph-energy-demand.git
  ```
- [x] Install UV (already installed via Homebrew)
- [x] Create shared virtual environment with UV (Python 3.10):
  ```bash
  cd ~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace
  uv venv --python 3.10
  source .venv/bin/activate
  ```
- [x] Install openph package with dev dependencies:
  ```bash
  uv pip install -e "./openph[dev]"
  ```

**Completion Criteria**:
- ✅ All 4 repositories created on GitHub
- ✅ All repositories cloned locally to `~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace/`
- ✅ UV installed
- ✅ Shared `.venv` created with UV and Python 3.10.18
- ✅ openph package installed in editable mode with dev tools
- ✅ All 105 tests passing

---

## Phase 1: Core Infrastructure 🔄 IN PROGRESS

**Goal**: Build the plugin architecture foundation in the `openph` core package.

### Step 1.1: Create Solver Protocol & Base Classes
**Files to create**: `openph/src/openph/solvers/base.py`

**Tasks**:
- [x] Copy `SolverPriority` enum from EXTENSIBILITY_PROPOSAL.md
- [x] Create `OpenPhSolver` Protocol with:
  - Properties: `solver_name`, `solver_version`, `solver_priority`, `depends_on`, `solver_description`
  - Method: `solve()`, `validate_dependencies()`
- [x] Write unit tests for protocol validation
- [x] Commit and push to `openph` repository

**Source Reference**: EXTENSIBILITY_PROPOSAL.md - "1. Solver Protocol with Dependencies"

**Success Criteria**:
- ✅ Protocol defines complete solver interface
- ✅ Type checking validates protocol compliance
- ✅ Tests verify protocol requirements (6 tests passing)

### Step 1.2: Create Attribute Protocol & Base Classes  
**Files to create**: `openph/src/openph/attributes/base.py`

**Tasks**:
- [x] Create `OpenPhAttribute` Protocol with:
  - Properties: `attribute_name`, `attribute_version`, `extends_classes`, `attribute_description`
  - Methods: `get_default_values()`, `validate_attribute_data()`, `serialize_data()`, `deserialize_data()`
- [x] Write unit tests for attribute protocol
- [x] Commit and push to `openph` repository

**Source Reference**: EXTENSIBILITY_PROPOSAL.md - "2. Data Model Attribute Extension Protocol"

**Success Criteria**:
- ✅ Protocol defines complete attribute interface
- ✅ Validation methods work correctly
- ✅ Tests verify protocol requirements (8 tests passing)

### Step 1.3: Create Solver Registry with Entry Point Discovery
**Files to create**: `openph/src/openph/solvers/registry.py`

**Tasks**:
- [x] Create `SolverInfo` dataclass
- [x] Implement `SolverRegistry` class with:
  - `discover_solvers()` - entry point discovery
  - `_calculate_execution_order()` - dependency resolution
  - `get_solver_class()` - solver retrieval
  - `get_execution_order()` - execution ordering
  - `list_solvers()` - registry inspection
- [x] Write comprehensive tests:
  - Entry point discovery
  - Dependency ordering
  - Circular dependency detection
- [x] Commit and push

**Source Reference**: EXTENSIBILITY_PROPOSAL.md - "2. Solver Registry with Entry Point Discovery"

**Success Criteria**:
- ✅ Entry points discovered from `pyproject.toml`
- ✅ Dependencies resolved in correct order
- ✅ Circular dependencies detected and raise errors
- ✅ All tests passing (20 tests passing)

### Step 1.4: Create Attribute Registry with Entry Point Discovery
**Files to create**: `openph/src/openph/attributes/registry.py`

**Tasks**:
- [x] Create `AttributeInfo` dataclass
- [x] Implement `AttributeRegistry` class with:
  - `discover_attributes()` - entry point discovery
  - `get_attribute_class()` - attribute retrieval
  - `list_attributes()` - registry inspection
- [x] Write unit tests for attribute discovery
- [x] Commit and push

**Source Reference**: EXTENSIBILITY_PROPOSAL.md - "3. Attribute Registry with Entry Point Discovery"

**Success Criteria**:
- ✅ Attribute entry points discovered correctly
- ✅ Registry manages multiple attributes
- ✅ Tests verify discovery mechanism (24 tests passing)

### Step 1.5: Create Solver Manager
**Files to create**: `openph/src/openph/solvers/manager.py`

**Tasks**:
- [x] Implement `SolverManager` class with:
  - `__init__()` - initialize with OpenPhModel reference
  - `get_solver()` - lazy solver instantiation
  - `solve()` - execute solver with dependencies
  - `solve_all()` - execute all solvers in order
  - `list_available_solvers()` - list solvers
  - `get_solver_info()` - detailed solver information
  - `reset_solved_state()` - clear cache
- [x] Write tests for:
  - Solver instantiation
  - Dependency resolution
  - Execution ordering
  - State management
- [x] Commit and push

**Source Reference**: EXTENSIBILITY_PROPOSAL.md - "Solver Manager with Data Access Control" (section 5)

**Success Criteria**:
- ✅ Solvers instantiated lazily
- ✅ Dependencies resolved automatically
- ✅ State tracked correctly
- ✅ All tests passing (20 tests passing)

### Step 1.6: Create Attribute Manager
**Files to create**: `openph/src/openph/attributes/manager.py`

**Tasks**:
- [x] Implement `AttributeManager` class with:
  - `__init__()` - initialize with OpenPhModel reference
  - `get_attribute_handler()` - lazy attribute instantiation
  - `get()` - retrieve attribute data
  - `set()` - update attribute data with validation
  - `list_available_attributes()` - list attributes
  - `get_attribute_info()` - detailed attribute information
- [x] Write tests for data management
- [x] Commit and push

**Source Reference**: EXTENSIBILITY_PROPOSAL.md - "4. Attribute Manager with Data Access Control"

**Success Criteria**:
- ✅ Attributes initialized with defaults
- ✅ Data validation works
- ✅ Get/set operations correct
- ✅ Tests verify all functionality (27 tests passing)

### Step 1.7: Copy Core Data Model Classes
**Files to copy from `ph-energy`** (paths shown using flat src/ pattern):
- `src/model/areas.py` → `openph-workspace/openph/src/areas.py`
- `src/model/climate.py` → `openph-workspace/openph/src/climate.py`
- `src/model/components.py` → `openph-workspace/openph/src/components.py`
- `src/model/constants.py` → `openph-workspace/openph/src/constants.py`
- `src/model/constructions.py` → `openph-workspace/openph/src/constructions.py`
- `src/model/enums.py` → `openph-workspace/openph/src/enums.py`
- `src/model/envelope.py` → `openph-workspace/openph/src/envelope.py`
- `src/model/ihg.py` → `openph-workspace/openph/src/ihg.py`
- `src/model/rooms.py` → `openph-workspace/openph/src/rooms.py`
- `src/model/settings.py` → `openph-workspace/openph/src/settings.py`
- `src/model/hvac/*` → `openph-workspace/openph/src/model/hvac/*`
- `src/model/loads/*` → `openph-workspace/openph/src/model/loads/*`
- `src/model/programs/*` → `openph-workspace/openph/src/model/programs/*`
- `src/model/schedules/*` → `openph-workspace/openph/src/model/schedules/*`

**Tasks**:
- [x] Copy all model files maintaining directory structure
- [x] Update imports to use `openph` package name
- [x] Remove any solver-specific code (move to solver packages)
- [x] Update type hints and references
- [x] Flatten src/ directory structure (removed extra openph/ nesting)
- [x] Configure pyproject.toml with explicit packages and package-dir mapping
- [x] Commit and push

**Success Criteria**:
- ✅ All model classes copied and functional (24 files, 4157 lines)
- ✅ Imports updated correctly (src.model → openph.model)
- ✅ No solver dependencies in model code
- ✅ Flat src/ structure implemented (src/model/, not src/openph/model/)
- ✅ Package configuration correct with explicit package list

**Note**: This step established the flat src/ pattern (src/attributes/, src/model/, src/solvers/) that all subsequent packages should follow.

### Step 1.8: Create OpenPhModel with Extension Managers
**Files to create**: `openph-workspace/openph/src/model/__init__.py` (flat src/ structure)

**Tasks**:
- [ ] Implement `OpenPhModel` class with:
  - Model data initialization (all copied model classes)
  - `SolverManager` initialization
  - `AttributeManager` initialization
  - `solve()` method for executing solvers
  - `list_solvers()`, `list_attributes()` convenience methods
  - `solver_info()`, `attribute_info()` inspection methods
- [ ] Add convenience properties for common solvers (optional)
- [ ] Write integration tests
- [ ] Commit and push

**Source Reference**: EXTENSIBILITY_PROPOSAL.md - "5. Updated OpenPhModel with Dual Extension Management"

**Success Criteria**:
- OpenPhModel instantiates correctly
- Both managers initialized
- Solver and attribute discovery works
- Integration tests pass

### Step 1.9: Create pyproject.toml for openph
**File to create**: `openph/pyproject.toml`

**Tasks**:
- [ ] Create complete `pyproject.toml` with:
  - Project metadata (name, version, description, authors)
  - Dependencies (phx, ph-units, honeybee_ph)
  - Development dependencies (pytest, ruff, black, etc.)
  - Empty entry points sections (solvers, attributes)
  - Build system configuration
- [ ] Test package installation with UV: `uv pip install -e .`
- [ ] Commit and push

**Source Reference**: EXTENSIBILITY_PROPOSAL.md - "6. Updated pyproject.toml with Dual Entry Points"

**Success Criteria**:
- Package installs without errors
- All dependencies resolved
- Entry point sections defined

### Step 1.10: Phase 1 Validation
**Integration tests**:

- [ ] Test solver registry discovers no solvers (empty entry points)
- [ ] Test attribute registry discovers no attributes (empty entry points)
- [ ] Test OpenPhModel instantiation
- [ ] Test manager initialization
- [ ] Verify package builds: `python -m build`
- [ ] Create Phase 1 release tag: `v0.1.0-alpha.1`

**Completion Criteria**:
- ✅ All core infrastructure in place
- ✅ Tests passing
- ✅ Package builds successfully
- ✅ Ready for solver migration

---

## Phase 2: Migrate Foundation Solvers 🔜 UPCOMING

**Goal**: Create `openph-ground` and `openph-solar` packages with working solvers.

### Step 2.1: Create openph-ground Package

#### Step 2.1.1: Setup Package Structure
**Repository**: `openph-ground`

**Tasks**:
- [ ] Create `pyproject.toml`:
  - Name: `openph-ground`
  - Dependencies: `openph>=0.1.0`
  - Entry point: `ground = "openph_ground.ground_solver:OpenPhGroundSolver"`
  - Configure with explicit packages list and package-dir mapping
- [ ] Create directory structure (flat src/ pattern):
  ```
  openph-workspace/openph-ground/    # Inside workspace container
  ├── pyproject.toml
  ├── README.md
  ├── src/                           # Flat structure - NO nested openph_ground/ folder
  │   ├── __init__.py                # Package root (openph_ground package)
  │   ├── ground_solver.py           # Module files directly in src/
  │   └── calc_periods.py
  └── tests/
      └── test_ground_solver.py
  ```
  **Note**: `src/` contains package modules directly (NOT `src/openph_ground/`)

#### Step 2.1.2: Copy Ground Solver Code
**Source**: `ph-energy/src/solvers/ground/`

**Tasks**:
- [ ] Copy `ground.py` → `src/ground_solver.py` (directly in src/)
- [ ] Copy `calc_periods.py` → `src/calc_periods.py`
- [ ] Copy supporting files to `src/` (floor types, etc.)
- [ ] Update imports to use `openph` instead of `ph-energy`
- [ ] Remove `TYPE_CHECKING` imports of `PhEnPHPP`
- [ ] Change to `OpenPhModel` references

#### Step 2.1.3: Implement OpenPhSolver Protocol
**File**: `src/ground_solver.py` (at src root, not nested)

**Tasks**:
- [ ] Rename class: `PhEnGround` → `OpenPhGroundSolver`
- [ ] Update `__init__` to accept `model: OpenPhModel`
- [ ] Add protocol properties:
  - `solver_name = "ground"`
  - `solver_version = "PHPP-10.4"`
  - `solver_priority = SolverPriority.FOUNDATION`
  - `depends_on = []`
- [ ] Implement `solve()` method:
  - Move calculation logic from `__post_init__`
  - Add `_solved` flag
  - Return self
- [ ] Update all properties to check `_solved` state
- [ ] Commit and push

#### Step 2.1.4: Write Tests
**Tasks**:
- [ ] Copy relevant tests from `ph-energy/tests/`
- [ ] Update test imports
- [ ] Add protocol compliance tests
- [ ] Add solver execution tests
- [ ] Run tests: `pytest`
- [ ] Commit and push

#### Step 2.1.5: Install and Validate
**Tasks**:
- [ ] Install in development mode with UV: 
  ```bash
  cd ~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace
  uv pip install -e ./openph-ground
  ```
- [ ] Test discovery:
  ```python
  from openph import OpenPhModel
  model = OpenPhModel()
  print(model.list_solvers())  # Should include 'ground'
  ```
- [ ] Test execution:
  ```python
  result = model.solve("ground")
  ```
- [ ] Create release tag: `v0.1.0-alpha.1`

### Step 2.2: Create openph-solar Package

**Follow same flat src/ structure as Step 2.1**:

#### Step 2.2.1: Setup Package Structure
- [ ] Create `pyproject.toml` with explicit packages and package-dir mapping
- [ ] Create directory structure (flat src/ pattern - NO nested openph_solar/)

#### Step 2.2.2: Copy Solar Radiation Solver Code
**Source**: `ph-energy/src/solvers/solar_radiation.py`

- [ ] Copy and rename to `src/solar_solver.py` (directly in src/)
- [ ] Update imports

#### Step 2.2.3: Implement OpenPhSolver Protocol
- [ ] Rename: `PhEnSolarRadiation` → `OpenPhSolarSolver`
- [ ] Add protocol properties
- [ ] Implement `solve()` method
- [ ] Commit and push

#### Step 2.2.4: Write Tests
- [ ] Copy and update tests
- [ ] Run tests
- [ ] Commit and push

#### Step 2.2.5: Install and Validate
- [ ] Install with UV: 
  ```bash
  cd ~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace
  uv pip install -e ./openph-solar
  ```
- [ ] Test discovery and execution
- [ ] Create release tag: `v0.1.0-alpha.1`

### Step 2.3: Phase 2 Validation

**Integration tests**:
- [ ] Install all packages: `openph`, `openph-ground`, `openph-solar`
- [ ] Test solver discovery finds both solvers
- [ ] Test execution order (both should be FOUNDATION priority)
- [ ] Test both solvers execute successfully
- [ ] Verify results match `ph-energy` outputs

**Completion Criteria**:
- ✅ Both foundation solvers working
- ✅ Entry point discovery functional
- ✅ Results validated against original implementation

---

## Phase 3: Migrate Energy Demand Solvers 🔜 UPCOMING

**Goal**: Create `openph-energy-demand` package with heating, cooling, and DHW solvers.

### Step 3.1: Setup Package Structure
**Repository**: `openph-energy-demand`

**Tasks**:
- [ ] Create `pyproject.toml`:
  - Name: `openph-energy-demand`
  - Dependencies: `openph>=0.1.0`, `openph-ground>=0.1.0`, `openph-solar>=0.1.0`
  - Entry points for 3 solvers: heating_demand, cooling_demand, dhw_demand
  - Configure with explicit packages list and package-dir mapping
- [ ] Create directory structure (flat src/ pattern):
  ```
  openph-workspace/openph-energy-demand/  # Inside workspace container
  ├── pyproject.toml
  ├── README.md
  ├── src/                                # Flat structure - NO nested openph_energy_demand/ folder
  │   ├── __init__.py                     # Package root (openph_energy_demand package)
  │   ├── heating_demand.py               # Module files directly in src/
  │   ├── cooling_demand.py
  │   ├── dhw_demand.py
  │   ├── calc_periods/                   # Subdirectories OK
  │   └── peak_load/
  └── tests/
  ```
  **Note**: `src/` contains package modules directly (NOT `src/openph_energy_demand/`)

### Step 3.2: Migrate Heating Demand Solver

#### Step 3.2.1: Copy Solver Code
**Source**: `ph-energy/src/solvers/heating_demand/`

- [ ] Copy `heating_demand.py` → `src/heating_demand.py` (directly in src/)
- [ ] Copy `calc_periods.py` → `src/calc_periods/heating_periods.py`
- [ ] Copy supporting files to `src/`
- [ ] Update imports

#### Step 3.2.2: Implement Protocol
- [ ] Rename: `PhEnHeatingDemand` → `OpenPhHeatingDemandSolver`
- [ ] Add protocol properties:
  - `solver_priority = SolverPriority.DEMAND`
  - `depends_on = ["ground", "solar_radiation"]`
- [ ] Implement `solve()` method
- [ ] Commit and push

#### Step 3.2.3: Write Tests
- [ ] Copy and update tests
- [ ] Run tests
- [ ] Commit and push

### Step 3.3: Migrate Cooling Demand Solver

**Follow same process as heating**:
- [ ] Copy `cooling_demand/` directory
- [ ] Rename to `OpenPhCoolingDemandSolver`
- [ ] Add dependencies: `["ground", "solar_radiation"]`
- [ ] Implement protocol
- [ ] Write tests
- [ ] Commit and push

### Step 3.4: Migrate DHW Demand Solver (if exists)

- [ ] Copy DHW solver code
- [ ] Implement protocol
- [ ] Write tests
- [ ] Commit and push

### Step 3.5: Install and Validate

**Tasks**:
- [ ] Install with UV: 
  ```bash
  cd ~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace
  uv pip install -e ./openph-energy-demand
  ```
- [ ] Test discovery:
  ```python
  model = OpenPhModel()
  print(model.list_solvers())  
  # Should include: ground, solar_radiation, heating_demand, cooling_demand
  ```
- [ ] Test dependency resolution:
  ```python
  result = model.solve("heating_demand")  
  # Should auto-solve ground and solar first
  ```
- [ ] Test execution order:
  ```python
  order = model.solvers.get_execution_order()
  print(order)
  # Should be: ['ground', 'solar_radiation', 'heating_demand', 'cooling_demand']
  ```
- [ ] Validate results match original implementation
- [ ] Create release tag: `v0.1.0-alpha.1`

### Step 3.6: Phase 3 Validation

**Integration tests**:
- [ ] Install all 4 packages together
- [ ] Test complete solver chain execution
- [ ] Verify dependency resolution
- [ ] Compare outputs with `ph-energy` for same input
- [ ] Run performance benchmarks

**Completion Criteria**:
- ✅ All energy demand solvers working
- ✅ Dependencies resolved correctly
- ✅ Results validated
- ✅ Performance acceptable

---

## Phase 4: Enhanced Features & Documentation 🔜 FUTURE

**Goal**: Add advanced features and comprehensive documentation.

### Step 4.1: Table Views Integration

**Tasks**:
- [ ] Copy `ph-energy/src/table_views/` to `openph/`
- [ ] Update table view functions to work with new solvers
- [ ] Add `get_table_views()` method to solver protocol
- [ ] Implement in all migrated solvers
- [ ] Write table view tests

### Step 4.2: Performance Monitoring

**Tasks**:
- [ ] Add timing decorator to `SolverManager.solve()`
- [ ] Track execution times per solver
- [ ] Add `get_performance_stats()` method
- [ ] Create performance reporting utilities
- [ ] Write performance tests

### Step 4.3: Solver Invalidation & Caching

**Tasks**:
- [ ] Implement `invalidate_solver()` method
- [ ] Add dependency-aware invalidation
- [ ] Create cache management utilities
- [ ] Write cache invalidation tests

### Step 4.4: Documentation

**Tasks**:
- [ ] Write comprehensive README for each repository
- [ ] Create developer guide for creating solvers
- [ ] Write user guide for using OpenPH
- [ ] Add API documentation
- [ ] Create example notebooks/scripts
- [ ] Document multi-repo development workflow

### Step 4.5: Example External Package

**Tasks**:
- [ ] Create `openph-economics` example package
- [ ] Implement `CostDataAttribute`
- [ ] Implement `LifecycleCostSolver`
- [ ] Write comprehensive documentation
- [ ] Publish as template for external developers

---

## Phase 5: Migration from HBJSON ⏸️ DEFERRED

**Goal**: Migrate or update the `from_HBJSON` workflow.

**Decision Point**: This phase is deferred until Phases 1-4 are complete. Will determine if:
1. HBJSON → OpenPhModel converter stays in core
2. HBJSON converter becomes separate package
3. Converter gets updated to new architecture

---

## Phase 6: Release & Deprecation 🎯 FINAL

**Goal**: Official v1.0.0 release and deprecate `ph-energy`.

### Step 6.1: Pre-Release Validation

**Tasks**:
- [ ] Run full test suite across all packages
- [ ] Validate against PHPP reference calculations
- [ ] Performance benchmarking
- [ ] Security audit
- [ ] Documentation review

### Step 6.2: Release v1.0.0

**Tasks**:
- [ ] Tag all repositories: `v1.0.0`
- [ ] Publish to PyPI with UV:
  - `cd openph && uv build && uv publish`
  - `cd openph-ground && uv build && uv publish`
  - `cd openph-solar && uv build && uv publish`
  - `cd openph-energy-demand && uv build && uv publish`
- [ ] Create GitHub releases with changelogs
- [ ] Announce release

### Step 6.3: Deprecate ph-energy

**Tasks**:
- [ ] Add deprecation notice to `ph-energy` README
- [ ] Update to recommend OpenPH packages
- [ ] Archive repository (read-only)
- [ ] Update all documentation links

---

## Development Workflow

### Daily Workflow
```bash
# Activate shared environment
cd ~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace
source .venv/bin/activate

# Work on specific package
cd openph
# Make changes...
pytest tests/
git commit -m "feat: add feature X"
git push

# Or work on a solver package
cd ../openph-ground
# Make changes...
pytest
git commit -m "feat: add feature X"
git push

# Test integration
cd ~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace
python -c "from openph import OpenPhModel; m = OpenPhModel(); print(m.list_solvers())"
```

### Testing Cross-Package Changes
```bash
# Install all packages in development mode with UV
cd ~/Dropbox/bldgtyp-00/00_PH_Tools/openph-workspace
uv pip install -e "./openph[dev]"
uv pip install -e ./openph-ground
uv pip install -e ./openph-solar
uv pip install -e ./openph-energy-demand

# Run integration tests
pytest openph/tests/integration/
```

### Release Workflow
```bash
# Update version in pyproject.toml
# Create git tag
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Build package with UV
uv build

# Publish to PyPI (when ready)
uv publish
```

---

## Progress Tracking

### Phase Completion Status

| Phase | Status | Completion Date |
|-------|--------|----------------|
| Phase 0: Repository Setup | ✅ Complete | Oct 14, 2025 |
| Phase 1: Core Infrastructure | 🔄 In Progress | - |
| Phase 2: Foundation Solvers | ⏸️ Not Started | - |
| Phase 3: Energy Demand Solvers | ⏸️ Not Started | - |
| Phase 4: Enhanced Features | ⏸️ Not Started | - |
| Phase 5: HBJSON Migration | ⏸️ Deferred | - |
| Phase 6: Release v1.0.0 | ⏸️ Not Started | - |

### Current Sprint

**Focus**: Phase 1 - Core Infrastructure  
**Target**: Create solver/attribute protocols, registries, and managers

**Next Steps**:
1. Create basic directory structure in `openph` repository
2. Create solver protocol (`OpenPhSolver`) 
3. Create attribute protocol (`OpenPhAttribute`)
4. Build solver registry with entry point discovery
5. Build attribute registry with entry point discovery

---

## Notes & Decisions

### Key Architectural Decisions
- ✅ Multi-repository strategy for modularity
- ✅ Shared virtual environment for local development
- ✅ Entry points for plugin discovery
- ✅ Dual extension system (solvers + attributes)
- ✅ Leave `ph-energy` unchanged during migration
- ✅ Python 3.10 minimum requirement (due to deployment environment constraints)

### Technical Requirements
- **Python Version**: Python 3.10+ (currently using 3.10.18 in development)
  - Deployment environment requires Python 3.10 compatibility
  - All packages configured with `requires-python = ">=3.10"`
  - Virtual environments created with Python 3.10.18
  - All 105 tests passing with Python 3.10

### Open Questions
- [ ] How to handle version compatibility across packages?
  - Proposal: Use semantic versioning with compatible ranges (e.g., `openph>=0.1.0,<0.2.0`)
- [ ] Should table views stay in core or become separate package?
  - Decision pending Phase 4
- [ ] HBJSON converter location?
  - Decision deferred to Phase 5

### Risk Mitigation
- **Risk**: Breaking changes during migration
  - **Mitigation**: Leave `ph-energy` untouched, build new separately
- **Risk**: Dependency version conflicts
  - **Mitigation**: Careful version pinning in `pyproject.toml`
- **Risk**: Loss of calculation accuracy during migration
  - **Mitigation**: Comprehensive validation tests against PHPP

---

## Resources

### Documentation References
- [EXTENSIBILITY_PROPOSAL.md](./EXTENSIBILITY_PROPOSAL.md) - Complete architecture specification
- [Python Packaging Guide](https://packaging.python.org/en/latest/) - Entry points and packaging
- [PEP 544](https://peps.python.org/pep-0544/) - Protocols and structural subtyping

### External Dependencies
- `phx` - Passive House data models
- `ph-units` - Unit conversion utilities
- `honeybee_ph` - Honeybee Passive House integration

---

**Ready to begin Phase 0!** 🚀

Should I create the first GitHub repository?
