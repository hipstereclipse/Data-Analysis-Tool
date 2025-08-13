        # === Analysis Configuration Section ===
        config_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        config_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            config_frame,
            text="⚙️ Analysis Configuration",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        # Comparison type selection
        comp_type_frame = ctk.CTkFrame(config_frame, corner_radius=6)
        comp_type_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            comp_type_frame,
            text="📊 Comparison Type",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(8, 2))
        
        self.comp_type_var = tk.StringVar(value="Smart Overlay")
        comp_type_values = [
            "Smart Overlay", "Side-by-Side", "Difference Analysis", 
            "Correlation Plot", "Statistical Summary", "Performance Comparison"
        ]
        self.comp_type_combo = ctk.CTkComboBox(
            comp_type_frame,
            variable=self.comp_type_var,
            values=comp_type_values,
            width=int(dialog_width * 0.32),
            height=30,
            corner_radius=6,
            command=self._on_comparison_type_change
        )
        self.comp_type_combo.pack(padx=10, pady=(0, 5))
        
        # Description for comparison type
        self.comp_type_desc = ctk.CTkLabel(
            comp_type_frame,
            text="Intelligent overlay with auto-scaling and optimal color selection",
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray40"),
            wraplength=int(dialog_width * 0.32)
        )
        self.comp_type_desc.pack(anchor="w", padx=10, pady=(0, 8))
        
        # Time alignment options
        align_frame = ctk.CTkFrame(config_frame, corner_radius=6)
        align_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            align_frame,
            text="⏱️ Time Alignment",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(8, 2))
        
        self.time_align_var = tk.StringVar(value="Auto-Detect")
        align_values = [
            "Auto-Detect", "None", "Start Times", "Peak Alignment", 
            "Cross-Correlation", "Custom Offset"
        ]
        self.time_align_combo = ctk.CTkComboBox(
            align_frame,
            variable=self.time_align_var,
            values=align_values,
            width=int(dialog_width * 0.32),
            height=30,
            corner_radius=6,
            command=self._on_alignment_change
        )
        self.time_align_combo.pack(padx=10, pady=(0, 5))
        
        # Alignment description
        self.align_desc = ctk.CTkLabel(
            align_frame,
            text="Smart alignment detection based on data characteristics",
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray40"),
            wraplength=int(dialog_width * 0.32)
        )
        self.align_desc.pack(anchor="w", padx=10, pady=(0, 8))
        
        # Advanced options
        advanced_frame = ctk.CTkFrame(config_frame, corner_radius=6)
        advanced_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            advanced_frame,
            text="🔬 Advanced Options",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(8, 5))
        
        # Confidence level
        confidence_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        confidence_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        confidence_label_frame = ctk.CTkFrame(confidence_frame, fg_color="transparent")
        confidence_label_frame.pack(fill="x")
        confidence_label_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            confidence_label_frame,
            text="Confidence Level:",
            font=ctk.CTkFont(size=11)
        ).grid(row=0, column=0, sticky="w")
        
        self.confidence_label = ctk.CTkLabel(
            confidence_label_frame,
            text="95%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#1E40AF", "#3B82F6")
        )
        self.confidence_label.grid(row=0, column=1, sticky="e")
        
        self.confidence_var = tk.DoubleVar(value=0.95)
        confidence_slider = ctk.CTkSlider(
            confidence_frame,
            from_=0.8,
            to=0.99,
            variable=self.confidence_var,
            width=int(dialog_width * 0.28),
            height=20,
            number_of_steps=19
        )
        confidence_slider.pack(pady=(5, 5))
        
        # Smart toggles
        toggles_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        self.auto_analysis_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            toggles_frame,
            text="🤖 Auto-update analysis",
            variable=self.auto_analysis_var,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", pady=2)
        
        # === Action Buttons ===
        button_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Main action buttons
        main_buttons = ctk.CTkFrame(button_frame, fg_color="transparent")
        main_buttons.pack(fill="x", padx=15, pady=15)
        
        self.run_button = ctk.CTkButton(
            main_buttons,
            text="🚀 Run Analysis",
            command=self.run_comparison_analysis,
            width=int(dialog_width * 0.32),
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#1E40AF", "#3B82F6"),
            hover_color=("#1E3A8A", "#2563EB")
        )
        self.run_button.pack(fill="x", pady=(0, 8))
        
        # Quick action buttons row
        quick_actions = ctk.CTkFrame(main_buttons, fg_color="transparent")
        quick_actions.pack(fill="x")
        quick_actions.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkButton(
            quick_actions,
            text="⚡ Quick",
            command=self._quick_compare,
            width=int(dialog_width * 0.09),
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=10)
        ).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        
        ctk.CTkButton(
            quick_actions,
            text="📋 Copy",
            command=self._copy_results,
            width=int(dialog_width * 0.09),
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=10)
        ).grid(row=0, column=1, padx=2, sticky="ew")
        
        ctk.CTkButton(
            quick_actions,
            text="🔄 Reset",
            command=self._reset_comparison,
            width=int(dialog_width * 0.09),
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=10)
        ).grid(row=0, column=2, padx=(3, 0), sticky="ew")
        
        # === RIGHT COLUMN: Results and Visualization ===
        right_panel = ctk.CTkFrame(
            main_container,
            corner_radius=10
        )
        right_panel.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # Results header with status
        results_header = ctk.CTkFrame(right_panel, height=50, corner_radius=8)
        results_header.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        results_header.grid_propagate(False)
        results_header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            results_header,
            text="📊 Analysis Results & Visualization",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=12, sticky="w")
        
        # Dynamic status indicator
        self.status_label = ctk.CTkLabel(
            results_header,
            text="🟡 Ready for analysis",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray40")
        )
        self.status_label.grid(row=0, column=1, padx=15, pady=12, sticky="e")
        
        # Tabbed results with intelligent height based on screen
        results_height = max(500, dialog_height - 250)
        
        self.results_tabview = ctk.CTkTabview(
            right_panel,
            height=results_height,
            corner_radius=8
        )
        self.results_tabview.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # === Visualization Tab ===
        viz_tab = self.results_tabview.add("📈 Visualization")
        
        # Plot container with scrolling for large plots
        self.comparison_plot_frame = ctk.CTkScrollableFrame(
            viz_tab,
            corner_radius=6
        )
        self.comparison_plot_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message
        initial_viz_msg = ctk.CTkLabel(
            self.comparison_plot_frame,
            text="🎯 Select two series and run analysis\nto see intelligent visualization",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40"),
            justify="center"
        )
        initial_viz_msg.pack(expand=True, pady=50)
        
        # === Statistics Tab ===
        stats_tab = self.results_tabview.add("📊 Statistics")
        
        self.comparison_results = ctk.CTkTextbox(
            stats_tab,
            corner_radius=6,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.comparison_results.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === AI Insights Tab ===
        insights_tab = self.results_tabview.add("🧠 AI Insights")
        
        self.insights_text = ctk.CTkTextbox(
            insights_tab,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.insights_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure event handlers for intelligent behavior
        confidence_slider.configure(command=self._update_confidence_label)
        
        # Initialize with smart defaults
        self.root.after(100, self._initialize_smart_defaults)
