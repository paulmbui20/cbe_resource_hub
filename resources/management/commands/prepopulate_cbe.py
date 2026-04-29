from django.core.management.base import BaseCommand
from django.db import transaction

from resources.models import EducationLevel, Grade, LearningArea


class Command(BaseCommand):
    help = "Prepopulate Kenyan CBC (CBE) curriculum structure (@ 2026 aligned)."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING("📚 Populating CBE Curriculum (Kenya as at 2026)..."))

        # --------------------------------------------------
        # 1. EDUCATION LEVELS + GRADES (CBC STRUCTURE)
        # --------------------------------------------------
        curriculum_structure = [
            ("Pre-Primary", ["PP1", "PP2"]),
            ("Lower Primary", ["Grade 1", "Grade 2", "Grade 3"]),
            ("Upper Primary", ["Grade 4", "Grade 5", "Grade 6"]),
            ("Junior School", ["Grade 7", "Grade 8", "Grade 9"]),
            ("Senior School", ["Grade 10", "Grade 11", "Grade 12"]),
        ]

        level_map = {}
        lvl_created, grd_created = 0, 0

        for lvl_idx, (level_name, grades) in enumerate(curriculum_structure):
            level, created = EducationLevel.objects.get_or_create(
                name=level_name,
                defaults={"order": lvl_idx},
            )
            level_map[level_name] = level

            if created:
                lvl_created += 1

            for g_idx, grade_name in enumerate(grades):
                _, g_created = Grade.objects.get_or_create(
                    level=level,
                    name=grade_name,
                    defaults={"order": g_idx},
                )
                if g_created:
                    grd_created += 1

        # --------------------------------------------------
        # 2. LEARNING AREAS (CBC-ALIGNED BY LEVEL)
        # --------------------------------------------------

        learning_areas_by_stage = {
            # PRE-PRIMARY (PP1–PP2)
            "Pre-Primary": [
                "Language Activities",
                "Mathematical Activities",
                "Environmental Activities",
                "Psychomotor and Creative Activities",
                "Religious Education Activities",
            ],

            # LOWER PRIMARY (GRADE 1–3)
            "Lower Primary": [
                "English",
                "Kiswahili",
                "Mathematics",
                "Environmental Activities",
                "Hygiene and Nutrition",
                "Religious Education",
                "Movement and Creative Activities",
            ],

            # UPPER PRIMARY (GRADE 4–6)
            "Upper Primary": [
                "English",
                "Kiswahili",
                "Mathematics",
                "Science and Technology",
                "Social Studies",
                "Agriculture",
                "Religious Education",
                "Creative Arts",
                "Physical and Health Education",
            ],

            # JUNIOR SCHOOL (GRADE 7–9)
            "Junior School": [
                "English",
                "Kiswahili",
                "Mathematics",
                "Integrated Science",
                "Health Education",
                "Pre-Technical Studies",
                "Social Studies",
                "Religious Education",
                "Business Studies",
                "Agriculture",
                "Life Skills Education",
                "Sports and Physical Education",
                "Visual Arts",
                "Performing Arts",
                "Computer Science",
            ],

            # SENIOR SCHOOL (PATHWAY-BASED PREP)
            "Senior School": [
                # STEM pathway
                "Pure Mathematics",
                "Applied Mathematics",
                "Physics",
                "Chemistry",
                "Biology",
                "Computer Science",

                # Arts & Sports
                "Fine Arts",
                "Music and Dance",
                "Theatre and Film",
                "Sports Science",

                # Social Sciences
                "History and Citizenship",
                "Geography",
                "Business Studies",
                "Economics",
                "Religious Studies",
                "Foreign Languages",
            ],
        }

        # Flatten + deduplicate
        all_learning_areas = sorted({
            la.strip()
            for areas in learning_areas_by_stage.values()
            for la in areas
        })

        la_created = 0
        for name in all_learning_areas:
            _, created = LearningArea.objects.get_or_create(name=name)
            if created:
                la_created += 1

        # --------------------------------------------------
        # OUTPUT SUMMARY
        # --------------------------------------------------
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Education Levels: {len(curriculum_structure)} ({lvl_created} created)"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Grades: {sum(len(v) for _, v in curriculum_structure)} ({grd_created} created)"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Learning Areas: {len(all_learning_areas)} ({la_created} created)"
            )
        )

        self.stdout.write(self.style.SUCCESS("🎉 CBC Curriculum prepopulation complete!"))
