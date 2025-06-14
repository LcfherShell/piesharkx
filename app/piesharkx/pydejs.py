import re, os, sys, uuid, json
from .handler.error_handler import Handlerr
from .handler.requests_ansyc import REQUESTS
from .handler import OrderedDict, SelectType, create_secure_memory
from multiprocessing import Process
import asyncio, time, timeit
from urllib.parse import urlparse
    
__all__ = ["PY_deJS"]
Struct = create_secure_memory()
libs_version, libs_limit, all_libs = [ "https://api.cdnjs.com/libraries/{filename}?fields=versions", "https://api.cdnjs.com/libraries?search={filename}&fields=filename&limit={num}", "https://api.cdnjs.com/libraries?limit={num}" ]

def sanitize_string(text: str) -> str:
    # Ganti semua non-word character dan spasi dengan '_'
    return re.sub(r'[^\w]', '_', text.strip())

class PY_deJS(SelectType):
    def __init__(self):
        super(PY_deJS, self).__init__()
        self.map_tokens = {}  # Changed to dict for multiple tokens
        self.app = REQUESTS()
        self.json = self.Dict_
        self.jnodes = []  # Changed to list for multiple nodes
        self.selected_modules = []  # Track selected modules
        self.nested_structure = {}  # New nested structure storage

    def js_map(self, maps, module_name):
        try:
            filename = re.findall(r'\/([a-zA-Z0-9_]*)\.[a-zA-Z]*\"$', maps)[0]
            extention = re.findall(r'([a-zA-Z]*)\"$', maps)[0]
        except:
            path = urlparse(maps).path
            filename, extention = os.path.splitext(path)

        if filename in maps and extention.replace('.', '') == 'js':
            js_map_token = str(uuid.uuid3(uuid.NAMESPACE_DNS, f'cdnjs.cloudflare.com-{module_name}'))
            self.map_tokens[module_name] = js_map_token
        else:
            self.map_tokens[module_name] = str(uuid.uuid4())

    def requests(self, search, limit, select=None):
        if select:
            if isinstance(select, str):
                if select.lower() == "all":
                    maps = all_libs
                elif select.lower() == "select":
                    maps  = libs_limit
        else:
            if select == None or select.strip() == '':
                maps = all_libs
        return maps.format(filename=search, num=limit)

    def get(self, search, limit=4, select='select'):
        """
        Enhanced get method to handle multiple modules with version details
        """
        if limit <= 2:
            assert 0 == 0
        
        # Handle multiple search terms
        if isinstance(search, str):
            search_terms = [search.strip()]
        elif isinstance(search, list):
            search_terms = [s.strip() for s in search if s.strip()]
        else:
            raise ValueError("Search parameter must be string or list of strings")

        loop = asyncio.get_event_loop()
        
        # Prepare requests for all search terms
        request_urls = []
        for term in search_terms:
            # Get library info with versions
            lib_url = libs_version.format(filename=term)
            request_urls.append(lib_url)
        
        min_loop = request_urls.__len__()
        max_loop = min_loop + 1
        
        # Make async requests for all modules
        responses = loop.run_until_complete(self.app.async_requests(request_urls, min_loop=min_loop, max_loop=max_loop))
        
        # Process responses
        self.json = []
        for i, response in enumerate(responses):
            try:
                if response.headers.get('Content-Type', "app/html").lower().count("/json") <= 0:
                    continue
                response_data = response.json()
                if response_data:
                    response_data['_search_term'] = search_terms[i]
                    self.json.append(response_data)
            except:
                pass

    def _categorize_files(self, files):
        """
        Categorize files by type (min, css, regular js, etc.)
        """
        categorized = {
            'min': [],
            'css': [],
            'regular': [],
            'map': [],
            'other': []
        }
        
        for file_url in files:
            filename = os.path.basename(urlparse(file_url).path).lower()
            
            if '.min.js' in filename:
                categorized['min'].append(file_url)
            elif '.min.css' in filename:
                categorized['css'].append(file_url)
            elif '.css' in filename:
                categorized['css'].append(file_url)
            elif '.js.map' in filename:
                categorized['map'].append(file_url)
            elif '.js' in filename:
                categorized['regular'].append(file_url)
            else:
                categorized['other'].append(file_url)
        
        return categorized

    def _generate_file_variants(self, module_name, base_url, all_files):
        """
        Generate different file variants for a module
        """
        variants = {}
        categorized = self._categorize_files(all_files)
        
        # Generate variant names based on file types
        if categorized['min']:
            variants[f"{module_name}min"] = categorized['min'][0]
            
        if categorized['css']:
            variants[f"{module_name}css"] = categorized['css'][0]
            
        if categorized['regular']:
            variants[f"{module_name}browser"] = categorized['regular'][0]
            
        if categorized['map']:
            variants[f"{module_name}map"] = categorized['map'][0]
            
        # Add main/latest version
        variants[f"{module_name}latest"] = base_url
        
        # Add additional variants if multiple files of same type exist
        if len(categorized['min']) > 1:
            for i, url in enumerate(categorized['min'][1:], 1):
                variants[f"{module_name}min{i+1}"] = url
                
        if len(categorized['css']) > 1:
            for i, url in enumerate(categorized['css'][1:], 1):
                variants[f"{module_name}css{i+1}"] = url
                
        if len(categorized['regular']) > 1:
            for i, url in enumerate(categorized['regular'][1:], 1):
                variants[f"{module_name}browser{i+1}"] = url
        
        return variants

    def select(self, version=None, modules=None, include_all_variants=True):
        """
        Enhanced select method with nested structure support
        version: specific version to select (default: latest)
        modules: list of specific modules to select
        include_all_variants: whether to include all file variants
        """
        if len(self.json) == 0:
            return
        
        self.jnodes = []
        self.selected_modules = []
        self.nested_structure = {}
        
        # Normalize modules parameter
        if modules is None:
            target_modules = None
        elif isinstance(modules, str):
            target_modules = [modules]
        elif isinstance(modules, list):
            target_modules = modules
        else:
            target_modules = [str(modules)]
        
        # Get all available modules
        all_module_names = [data_json.get('_search_term') for data_json in self.json if data_json.get('_search_term')]
        
        # Determine which modules to process
        if target_modules:
            modules_to_process = target_modules
        else:
            modules_to_process = all_module_names
        
        # Process each module
        for module_data in self.json:
            module_name = module_data.get('_search_term')
            
            if module_name in modules_to_process:
                # Get version info
                versions = module_data.get('versions', [])
                if not versions:
                    continue
                
                # Select version
                if version and version in versions:
                    selected_version = version
                else:
                    selected_version = versions[0]  # Latest version
                
                # Get base URL for the selected version
                base_url = f"https://cdnjs.cloudflare.com/ajax/libs/{module_data.get('name', module_name)}/{selected_version}"
                
                # Get all files for this version (this would need API call to get file list)
                # For now, we'll generate common variants
                common_files = [
                    f"{base_url}/{module_name}.min.js",
                    f"{base_url}/{module_name}.js",
                    f"{base_url}/{module_name}.min.css",
                    f"{base_url}/{module_name}.css",
                    f"{base_url}/{module_name}.js.map"
                ]
                
                if include_all_variants:
                    variants = self._generate_file_variants(module_name, base_url, common_files)
                else:
                    # Just include min and regular versions
                    variants = {
                        f"{module_name}min": f"{base_url}/{module_name}.min.js",
                        f"{module_name}browser": f"{base_url}/{module_name}.js"
                    }
                
                # Store in nested structure
                self.nested_structure[module_name] = variants
                
                # Keep backward compatibility
                node_data = {
                    'name': module_data.get('name', module_name),
                    'filename': module_name,
                    'latest': variants.get(f"{module_name}min", variants.get(f"{module_name}latest", base_url)),
                    'description': module_data.get('description', ''),
                    'version': selected_version,
                    'variants': variants
                }
                
                self.jnodes.append(node_data)
                self.selected_modules.append(module_name)

    def select_all(self, version=None, include_all_variants=True):
        """
        Select all modules with nested structure
        """
        self.select(version=version, modules=None, include_all_variants=include_all_variants)

    def select_specific(self, modules, version=None, include_all_variants=True):
        """
        Select specific modules with nested structure
        """
        self.select(version=version, modules=modules, include_all_variants=include_all_variants)

    @property
    def nested_links(self):
        """
        Return nested structure of all links
        Example: {"jquery": {"jquerymin": "url", "jquerybrowser": "url", "jquerycss": "url"}}
        """
        return self.nested_structure

    @property
    def links(self):
        """
        Return list of all selected module links (main/latest versions)
        """
        return [node.get('latest', '') for node in self.jnodes]

    @property
    def link(self):
        """
        Return single link (backward compatibility) - returns first link
        """
        if self.jnodes:
            return self.jnodes[0].get('latest', '')
        return ''

    @property
    def scripts(self):
        """
        Return list of all script tags for selected modules - Enhanced version
        """
        script_tags = []
        for i, node in enumerate(self.jnodes):
            module_name = self.selected_modules[i] if i < len(self.selected_modules) else f'module_{i}'
            variants = node.get('variants', {})
            
            # Generate script tags for JS variants
            for variant_name, url in variants.items():
                if url.endswith('.js') or url.endswith('.min.js'):
                    self.js_map(url, f"{module_name}_{variant_name}")
                    
                    script_tag = '<script type="text/javascript" src="{script}" jnode="{jnode}" data-module="{module}" data-variant="{variant}"></script>'.format(
                        script=url,
                        jnode=self.map_tokens.get(f"{module_name}_{variant_name}", ''),
                        module=module_name,
                        variant=variant_name
                    )
                    script_tags.append(script_tag)
        
        return script_tags

    @property
    def css_links(self):
        """
        Return list of all CSS link tags for selected modules
        """
        css_tags = []
        for i, node in enumerate(self.jnodes):
            module_name = self.selected_modules[i] if i < len(self.selected_modules) else f'module_{i}'
            variants = node.get('variants', {})
            
            # Generate link tags for CSS variants
            for variant_name, url in variants.items():
                if url.endswith('.css') or url.endswith('.min.css'):
                    css_tag = '<link rel="stylesheet" type="text/css" href="{css}" data-module="{module}" data-variant="{variant}">'.format(
                        css=url,
                        module=module_name,
                        variant=variant_name
                    )
                    css_tags.append(css_tag)
        
        return css_tags

    @property
    def scripts_safe(self):
        """
        Return nested dictionary of script tags with module names as keys
        """
        script_dict = {}
        for i, node in enumerate(self.jnodes):
            module_name = self.selected_modules[i] if i < len(self.selected_modules) else f'module_{i}'
            variants = node.get('variants', {})
            
            module_scripts = {}
            for variant_name, url in variants.items():
                if url.endswith('.js') or url.endswith('.min.js'):
                    self.js_map(url, f"{module_name}_{variant_name}")
                    
                    script_tag = '<script type="text/javascript" src="{script}" jnode="{jnode}" data-module="{module}" data-variant="{variant}"></script>'.format(
                        script=url,
                        jnode=self.map_tokens.get(f"{module_name}_{variant_name}", ''),
                        module=module_name,
                        variant=variant_name
                    )
                    module_scripts[sanitize_string(variant_name)] = script_tag
            
            if module_scripts:
                script_dict[sanitize_string(module_name)] = Struct(**module_scripts)
        
        return Struct(**script_dict)

    @property
    def css_safe(self):
        """
        Return nested dictionary of CSS link tags with module names as keys
        """
        css_dict = {}
        for i, node in enumerate(self.jnodes):
            module_name = self.selected_modules[i] if i < len(self.selected_modules) else f'module_{i}'
            variants = node.get('variants', {})
            
            module_css = {}
            for variant_name, url in variants.items():
                if url.endswith('.css') or url.endswith('.min.css'):
                    css_tag = '<link rel="stylesheet" type="text/css" href="{css}" data-module="{module}" data-variant="{variant}">'.format(
                        css=url,
                        module=module_name,
                        variant=variant_name
                    )
                    module_css[sanitize_string(variant_name)] = css_tag
            
            if module_css:
                css_dict[sanitize_string(module_name)] = Struct(**module_css)
        
        return Struct(**css_dict)

    @property
    def script(self):
        """
        Return single script tag (backward compatibility) - returns first script
        """
        scripts = self.scripts
        return scripts[0] if scripts else ''

    @property
    def combined_scripts(self):
        """
        Return all script tags combined as a single string
        """
        return '\n'.join(self.scripts)

    @property
    def combined_css(self):
        """
        Return all CSS link tags combined as a single string
        """
        return '\n'.join(self.css_links)

    def get_module_info(self):
        """
        Return detailed information about selected modules with nested structure
        """
        info = []
        for i, node in enumerate(self.jnodes):
            module_name = self.selected_modules[i] if i < len(self.selected_modules) else f'module_{i}'
            
            module_info = {
                'name': module_name,
                'filename': node.get('filename', ''),
                'description': node.get('description', ''),
                'version': node.get('version', ''),
                'latest': node.get('latest', ''),
                'variants': node.get('variants', {}),
                'tokens': {}
            }
            
            # Generate tokens for each variant
            for variant_name, url in node.get('variants', {}).items():
                token_key = f"{module_name}_{variant_name}"
                if token_key not in self.map_tokens:
                    self.js_map(url, token_key)
                module_info['tokens'][variant_name] = self.map_tokens.get(token_key, '')
            
            info.append(module_info)
        
        return info

    def get_nested_structure(self):
        """
        Return the complete nested structure
        Example: {"jquery": {"jquerymin": "url", "jquerybrowser": "url", "jquerycss": "url"}}
        """
        return self.nested_structure

    def get_flat_structure(self):
        """
        Return flattened structure for easier access
        """
        flat = {}
        for module_name, variants in self.nested_structure.items():
            for variant_name, url in variants.items():
                flat[f"{module_name}.{variant_name}"] = url
        return flat

    def clear_selection(self):
        """
        Clear current selection
        """
        self.jnodes = []
        self.selected_modules = []
        self.map_tokens = {}
        self.nested_structure = {}

    def filter_by_type(self, file_type):
        """
        Filter nested structure by file type
        file_type: 'js', 'css', 'min', 'map'
        """
        filtered = {}
        for module_name, variants in self.nested_structure.items():
            module_filtered = {}
            for variant_name, url in variants.items():
                if file_type == 'js' and (url.endswith('.js') or url.endswith('.min.js')):
                    module_filtered[variant_name] = url
                elif file_type == 'css' and (url.endswith('.css') or url.endswith('.min.css')):
                    module_filtered[variant_name] = url
                elif file_type == 'min' and '.min.' in url:
                    module_filtered[variant_name] = url
                elif file_type == 'map' and url.endswith('.map'):
                    module_filtered[variant_name] = url
            
            if module_filtered:
                filtered[module_name] = module_filtered
        
        return filtered