package org.psem2m.utilities.teststools;

import java.util.logging.Level;

import junit.framework.TestCase;

import org.psem2m.utilities.CXDateTime;
import org.psem2m.utilities.CXJavaRunContext;

/**
 * @author isandlaTech - ogattaz
 * 
 */
public class CQualityTestBase extends TestCase {

	final static String SEP_TIME = ":";

	public final static String[] START_ARGS = { "-junit" };

	/**
	 * @param aWho
	 * @param aLevel
	 * @param aMethod
	 * @param aFormat
	 * @param aArgs
	 * @return
	 */
	private String formatLog(final Object aWho, final Level aLevel,
			final CharSequence aMethod, final CharSequence aFormat,
			final Object... aArgs) {

		return "[" + formatTime(System.currentTimeMillis()) + "][" + aLevel
				+ "][" + Thread.currentThread().getName() + "]"
				+ aWho.getClass().getSimpleName() + ":" + aMethod.toString()
				+ " | " + String.format(String.valueOf(aFormat), aArgs);
	}

	/**
	 * @param aMillis
	 * @return
	 */
	private String formatTime(final long aMillis) {
		return CXDateTime.time2StrHHMMSSmmm(aMillis, SEP_TIME);

	}

	/**
	 * @param aWho
	 * @param aLevel
	 * @param aMethod
	 * @param aFormat
	 * @param aArgs
	 */
	protected void log(final Object aWho, final Level aLevel,
			final CharSequence aMethod, final CharSequence aFormat,
			final Object... aArgs) {
		System.out.println(formatLog(aWho, aLevel, aMethod, aFormat, aArgs));
	}

	/**
	 * @param aWho
	 * @param aWhat
	 * @param aFormat
	 * @param aArgs
	 */
	protected void logDebug(final Object aWho, final CharSequence aFormat,
			final Object... aArgs) {
		log(aWho, Level.SEVERE, CXJavaRunContext.getCallingMethod(), aFormat,
				aArgs);
	}

	/**
	 * @param aWho
	 * @param aWhat
	 * @param aFormat
	 * @param aArgs
	 */
	protected void logFine(final Object aWho, final CharSequence aFormat,
			final Object... aArgs) {
		log(aWho, Level.FINE, CXJavaRunContext.getCallingMethod(), aFormat,
				aArgs);
	}

	/**
	 * @param aWho
	 * @param aWhat
	 * @param aFormat
	 * @param aArgs
	 */
	protected void logInfo(final Object aWho, final CharSequence aFormat,
			final Object... aArgs) {
		log(aWho, Level.INFO, CXJavaRunContext.getCallingMethod(), aFormat,
				aArgs);
	}

	/**
	 * @param aWho
	 * @param aMethodName
	 */
	protected void logMethodName(final Object aWho,
			final CharSequence aMethodName) {
		log(aWho, Level.INFO, aMethodName, null);
	}

}
