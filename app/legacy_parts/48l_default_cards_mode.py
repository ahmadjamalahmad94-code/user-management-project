# 48l_default_cards_mode.py
# قاعدة افتراضية: كل مشترك جديد يحصل على "نظام البطاقات" كطريقة اتصال.
# - يطبّقها على المشتركين الحاليين الذين بدون طريقة (one-time UPDATE)
# - يضيف trigger للمشتركين الجدد لاحقًا

CARDS_METHOD_LABEL = "نظام البطاقات"


def _backfill_existing_beneficiaries():
    """تحديث المشتركين الحاليين الذين بدون internet_method محدّد."""
    try:
        # توجيهي: لا يحتاج (مقفل على البطاقات قواعديًا)
        # جامعي: لو internet_method فاضي، عيّن البطاقات
        execute_sql(
            """
            UPDATE beneficiaries
            SET university_internet_method = %s
            WHERE user_type = 'university'
              AND (university_internet_method IS NULL OR university_internet_method = '')
            """,
            [CARDS_METHOD_LABEL],
        )
        # فري لانسر
        execute_sql(
            """
            UPDATE beneficiaries
            SET freelancer_internet_method = %s
            WHERE user_type = 'freelancer'
              AND (freelancer_internet_method IS NULL OR freelancer_internet_method = '')
            """,
            [CARDS_METHOD_LABEL],
        )
    except Exception:
        pass


def _install_default_cards_trigger_sqlite():
    """trigger على SQLite يعيّن البطاقات كافتراضي للمشتركين الجدد."""
    try:
        execute_sql("DROP TRIGGER IF EXISTS trg_default_cards_method")
        execute_sql("""
        CREATE TRIGGER trg_default_cards_method
        AFTER INSERT ON beneficiaries
        WHEN
            (NEW.user_type = 'university' AND (NEW.university_internet_method IS NULL OR NEW.university_internet_method = ''))
            OR (NEW.user_type = 'freelancer' AND (NEW.freelancer_internet_method IS NULL OR NEW.freelancer_internet_method = ''))
        BEGIN
            UPDATE beneficiaries SET
                university_internet_method =
                    CASE WHEN NEW.user_type='university' AND (university_internet_method IS NULL OR university_internet_method='')
                         THEN 'نظام البطاقات' ELSE university_internet_method END,
                freelancer_internet_method =
                    CASE WHEN NEW.user_type='freelancer' AND (freelancer_internet_method IS NULL OR freelancer_internet_method='')
                         THEN 'نظام البطاقات' ELSE freelancer_internet_method END
            WHERE id = NEW.id;
        END
        """)
    except Exception:
        pass


def _install_default_cards_trigger_postgres():
    """trigger على PostgreSQL يعيّن البطاقات كافتراضي للمشتركين الجدد."""
    try:
        execute_sql("""
        CREATE OR REPLACE FUNCTION fn_default_cards_method() RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.user_type = 'university'
               AND (NEW.university_internet_method IS NULL OR NEW.university_internet_method = '') THEN
                NEW.university_internet_method := 'نظام البطاقات';
            END IF;
            IF NEW.user_type = 'freelancer'
               AND (NEW.freelancer_internet_method IS NULL OR NEW.freelancer_internet_method = '') THEN
                NEW.freelancer_internet_method := 'نظام البطاقات';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
        execute_sql("DROP TRIGGER IF EXISTS trg_default_cards_method ON beneficiaries")
        execute_sql("""
        CREATE TRIGGER trg_default_cards_method
        BEFORE INSERT ON beneficiaries
        FOR EACH ROW EXECUTE FUNCTION fn_default_cards_method();
        """)
    except Exception:
        pass


try:
    _backfill_existing_beneficiaries()
    if is_sqlite_database_url():
        _install_default_cards_trigger_sqlite()
    else:
        _install_default_cards_trigger_postgres()
except Exception:
    pass
